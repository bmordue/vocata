from base64 import b64decode
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..graph.authz import PUBLIC_ACTOR
from ..util.http import HTTPSignatureAuth


class ActivityPubActorMiddleware(BaseHTTPMiddleware):
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

        if "@" not in user:
            request.state.graph._logger.debug("Appending netloc to username")
            domain = request.url.netloc
            user = f"{user}@{domain}"

        actor = request.state.graph.get_actor_uri_by_acct(user)
        if not actor:
            raise KeyError("Account is not linked to an actor")
        request.state.graph._logger.debug("Authenticatin %s", actor)

        valid = request.state.graph.verify_actor_password(actor, password)
        if valid:
            return actor
        raise ValueError("Invalid password")

    async def determine_actor(self, request: Request) -> str:
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

        # Ensure the actor is on the graph for later authorization
        request.state.graph.pull(actor)
        return actor

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # FIXME fix timeout for real
        try:
            request.state.json = await request.json()
        except:
            pass

        try:
            request.state.actor = await self.determine_actor(request)
        except Exception as ex:
            return JSONResponse({"error": str(ex)}, 401)
        request.state.graph._logger.info("Actor was determined as %s", request.state.actor)

        request.state.subject = str(request.url).removesuffix("/")

        response = await call_next(request)

        return response
