# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from base64 import b64decode
from typing import Callable, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.types import ASGIApp

from ..graph.authz import PUBLIC_ACTOR, SESSION_KEY
from ..graph.activitypub import AP_CONTENT_TYPES
from ..util.http import HTTPSignatureAuth


def accepts_ap_types(request):
    # text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
    header = request.headers.get("Accept")
    accepts_raw = header.split(",")
    accepts = [v.split(";", 1)[0] for v in accepts_raw]
    return any([v in AP_CONTENT_TYPES for v in accepts])


class ActivityPubActorMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        pass_thru_paths: str | List | None = None,
    ):
        super().__init__(app)
        self.app = app
        if pass_thru_paths is None:
            pass_thru_paths = []
        elif isinstance(pass_thru_paths, str):
            pass_thru_paths = [pass_thru_paths]

        self.pass_thru_paths = pass_thru_paths

    def _get_actor_for_credentials(self, request, user, password):
        if "@" not in user:
            request.state.graph._logger.debug("Appending netloc to username")
            domain = request.url.netloc
            user = f"{user}@{domain}"

        actor = request.state.graph.get_canonical_uri(f"acct:{user}")
        if not actor:
            raise KeyError("Account is not linked to an actor")
        request.state.graph._logger.debug("Authenticated %s", actor)

        valid = request.state.graph.verify_actor_password(actor, password)
        if valid:
            return actor
        raise ValueError("Invalid password")

    async def determine_actor_from_http_signature(self, request: Request) -> str:
        key_id = await HTTPSignatureAuth.from_signed_request(request).verify_request(request)
        request.state.graph._logger.debug("Request is signed by key ID %s", key_id)

        if request.method == "POST" and "Digest" not in request.headers:
            raise KeyError("Digest header is missing")

        actor = request.state.graph.get_actor_by_key_id(key_id)
        if not actor:
            raise KeyError("Public key is not linked to an actor")
        return actor

    async def determine_actor_from_basic_auth(self, request: Request) -> str:
        request.state.graph._logger.debug("Doing HTTP Basic auth")
        credentials = request.headers["Authorization"].split(" ", 1)[1]
        user, password = b64decode(credentials).decode("utf-8").split(":", 1)

        actor = self._get_actor_for_credentials(request, user, password)
        return actor

    async def determine_actor_from_session(self, request: Request) -> str:
        request.state.graph._logger.debug("Doing Session auth")

        user = request.session.get(SESSION_KEY)
        if not user:
            raise KeyError("No user in session")

        actor = request.state.graph.get_canonical_uri(f"acct:{user}")
        if not actor:
            raise KeyError("Account is not linked to an actor")

        request.state.graph._logger.debug("Authenticated %s", actor)
        return actor

    async def determine_actor_from_form(self, request: Request) -> str:
        request.state.graph._logger.debug("Doing Form auth")

        form = await request.form()
        user = form.get("user")
        password = form.get("password")

        if not user:
            raise ValueError("Missing user value for authentication")

        actor = self._get_actor_for_credentials(request, user, password)
        # so that the session authenticates next time
        request.session[SESSION_KEY] = user
        return actor

    async def determine_actor(self, request: Request) -> str:
        actor = None
        if not accepts_ap_types(request):
            request.state.graph._logger.debug("Not an AP client! Try web auth...")
            try:
                actor = await self.determine_actor_from_session(request)
            except KeyError:
                request.state.graph._logger.debug("Could not get actor from session")
                pass
            try:
                actor = await self.determine_actor_from_form(request)
            except ValueError:
                request.state.graph._logger.debug("Could not get actor from form")
                pass

            if not actor:
                raise ValueError("Unauthorized")

            return actor

        actor = PUBLIC_ACTOR

        if "Signature" in request.headers:
            request.state.graph._logger.debug("Request has Signature header")
            actor = await self.determine_actor_from_http_signature(request)
        elif "Authorization" in request.headers:
            request.state.graph._logger.debug("Request has Authorization header")
            # FIXME catch and raise proper exception here
            scheme, parameters = request.headers["Authorization"].split(" ", 1)

            if scheme.lower() == "basic":
                actor = await self.determine_actor_from_basic_auth(request)
            elif scheme.lower() == "signature":
                actor = await self.determine_actor_from_http_signature(request)
        else:
            # Try the session, where a form-logged-in user will be stored
            if request.session is not None:
                try:
                    actor = await self.determine_actor_from_session(request)
                except KeyError:
                    pass

            # if we still havent found a non-public user, see if there's a
            # form submission. really this should be limited to requests
            # to /auth/signin but i don't have a good idea on how/where
            # to do that yet
            if actor == PUBLIC_ACTOR:
                actor = await self.determine_actor_from_form(request)

            request.state.graph.pull(actor)
        return actor

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # We need to read early because some clients have really short timeouts
        # FIXME try to avoid this
        request.state.body = await request.body()

        # is this a public path?
        public = any([request.url.path.startswith(p) for p in self.pass_thru_paths])

        # public request, send them through
        if public:
            request.state.actor = None
            response = await call_next(request)
            return response

        try:
            request.state.actor = await self.determine_actor(request)
        except Exception as ex:
            # if we found  an actor then we go on our way, but
            # if and exception was raised, check and see if the path is ok
            # to pass thru to anyway (ie public)
            # FIXME: Add to the graph somehow

            # non-AP client asking for an authenticated endpoint
            # send them to the login
            if not accepts_ap_types(request) and not public:
                response = RedirectResponse(f"/auth/signin?t={request.url.path}")
                return response

            return JSONResponse({"error": str(ex)}, 401)

        request.state.graph._logger.info("Actor was determined as %s", request.state.actor)

        request.state.subject = str(request.url).removesuffix("/")

        if request.state.graph.is_local_prefix(request.state.subject):
            prefix = request.state.graph.get_url_prefix(request.state.subject)
            if prefix not in request.state.used_prefixes:
                # Reset prefix endpoints if we didn't already do that
                endpoints = {
                    "proxyUrl": request.app.url_path_for("functional:proxy").make_absolute_url(
                        base_url=request.base_url
                    ),
                }
                request.state.graph.reset_prefix_endpoints(prefix, endpoints)

                request.state.used_prefixes.add(prefix)

        response = await call_next(request)

        return response
