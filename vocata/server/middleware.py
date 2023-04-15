from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..graph.authz import PUBLIC_ACTOR
from ..util.http import HTTPSignatureAuth


class ActivityPubActorMiddleware(BaseHTTPMiddleware):
    def determine_actor(self, request: Request) -> str:
        actor = PUBLIC_ACTOR

        if "Signature" in request.headers:
            request.state.graph._logger.debug("Request has Signature header")
            key_id = HTTPSignatureAuth.from_signed_request(request).verify_request(request)
            request.state.graph._logger.debug("Request is signed by key ID %s", key_id)

            actor = request.state.graph.get_actor_by_key_id(key_id)
            if not actor:
                raise KeyError("Public key is not linked to an actor")

        return actor

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.graph = request.app.state.graph

        try:
            request.state.actor = self.determine_actor(request)
        except Exception as ex:
            return JSONResponse({"error": str(ex)}, 401)
        request.state.graph._logger.info("Actor was determined as %s", request.state.actor)

        request.state.subject = str(request.url)

        response = await call_next(request)

        return response
