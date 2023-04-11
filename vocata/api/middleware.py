from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..data import PUBLIC_ACTOR, get_graph

class ActivityPubActorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.graph = get_graph()
        # FIXME implement
        request.state.actor = PUBLIC_ACTOR
        request.state.subject = str(request.url)

        response = await call_next(request)

        return response
