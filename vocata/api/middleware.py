from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ActivityPubActorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # FIXME implement; note: probably set to #Public?
        request.state.actor = None

        response = await call_next(request)

        return response
