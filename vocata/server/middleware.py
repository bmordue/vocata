# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from base64 import b64decode
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..graph.authz import PUBLIC_ACTOR, SESSION_KEY
from ..util.http import HTTPSignatureAuth


class DetermineActor:
    def __init__(self, required=False):
        self.actor_required = required

    def _get_actor_for_credentials(self, request, user, password):
        if "@" not in user:
            request.state.graph._logger.debug("Appending netloc to username")
            domain = request.url.netloc
            user = f"{user}@{domain}"

        with request.state.graph as graph:
            actor = graph.get_canonical_uri(f"acct:{user}")

        if not actor:
            if self.actor_required:
                raise KeyError("Account is not linked to an actor")
            return None

        request.state.graph._logger.debug("Authenticated %s", actor)

        with request.state.graph as graph:
            valid = graph.verify_actor_password(actor, password)

        if valid:
            return actor
        if self.actor_required:
            raise ValueError("Invalid password")

        return None

    async def from_http_signature(self, request: Request, required: bool = False) -> str:
        key_id = await HTTPSignatureAuth.from_signed_request(request).verify_request(request)
        request.state.graph._logger.debug("Request is signed by key ID %s", key_id)

        if request.method == "POST" and "Digest" not in request.headers:
            if self.actor_required or required:
                raise KeyError("Digest header is missing")
            return None

        with request.state.graph as graph:
            actor = graph.get_actor_by_key_id(key_id)
        if not actor:
            if self.actor_required or required:
                raise KeyError("Public key is not linked to an actor")
            return None

        return actor

    async def from_basic_auth(self, request: Request, required: bool = False) -> str:
        request.state.graph._logger.debug("Doing HTTP Basic auth")
        credentials = request.headers["Authorization"].split(" ", 1)[1]
        user, password = b64decode(credentials).decode("utf-8").split(":", 1)

        actor = self._get_actor_for_credentials(request, user, password)
        if not actor:
            if self.actor_required or required:
                raise KeyError("No actor ")
        return actor

    async def from_session(self, request: Request, required: bool = False) -> str:
        request.state.graph._logger.debug(f"Doing Session auth for {request.url.path}")

        user = request.session.get(SESSION_KEY)
        if not user:
            if self.actor_required or required:
                raise KeyError("No user in session")
            return None
        print(user)
        with request.state.graph as graph:
            actor = graph.get_canonical_uri(f"acct:{user}")

        if not actor:
            if self.actor_required or required:
                raise KeyError("Account is not linked to an actor")
            return None

        request.state.graph._logger.debug("Authenticated %s", actor)
        return actor

    async def from_form(self, request: Request, required: bool = False) -> str:
        form = await request.form()
        print(form)
        if not form:
            if self.actor_required or required:
                raise ValueError("Missing user value for authentication")
            else:
                return None

        user = form.get("user")
        password = form.get("password")

        if not user:
            if self.actor_required:
                raise ValueError("Missing user value for authentication")
            return None

        actor = self._get_actor_for_credentials(request, user, password)
        print(actor, user)
        # so that the session authenticates next time
        request.session[SESSION_KEY] = user
        return actor


class WebAuthMiddleware(BaseHTTPMiddleware):
    async def determine_actor(self, request: Request):
        # request.state.graph._logger.debug("WebAuthMiddleware.determine_actor()")
        # no actor required but get it from session or form if there is one
        da = DetermineActor()
        actor = await da.from_session(request)
        return actor or PUBLIC_ACTOR

    async def dispatch(self, request: Request, call_next: Callable):
        print(f"WebAuthMiddleware.dispatch path: {request.url.path} cookies: {request.cookies}")
        # request.state.graph._logger.debug(f"WebAuthMiddleware.dispatch() {actor}")
        actor = await self.determine_actor(request)
        request.state.actor = actor
        return await call_next(request)


class ActivityPubActorMiddleware(BaseHTTPMiddleware):
    async def determine_actor(self, request: Request) -> str:
        actor = PUBLIC_ACTOR

        da = DetermineActor(required=True)

        if "Signature" in request.headers:
            request.state.graph._logger.debug("Request has Signature header")
            actor = await da.from_http_signature(request)

        elif "Authorization" in request.headers:
            request.state.graph._logger.debug("Request has Authorization header")
            # FIXME catch and raise proper exception here
            scheme, parameters = request.headers["Authorization"].split(" ", 1)

            if scheme.lower() == "basic":
                actor = await da.from_basic_auth(request)
            elif scheme.lower() == "signature":
                actor = await da.from_http_signature(request)

        request.state.graph.pull(actor)
        return actor

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        print(f"ActivityPubActorMiddleware.dispatch cookies{request.cookies}")

        # We need to read early because some clients have really short timeouts
        # FIXME try to avoid this
        request.state.body = await request.body()

        try:
            request.state.actor = await self.determine_actor(request)
        except Exception as ex:
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
