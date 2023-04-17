from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..graph.authz import AccessMode, PUBLIC_ACTOR


class ActivityPubEndpoint(HTTPEndpoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _check_auth(
        self, request: Request, mode: AccessMode = AccessMode.READ
    ) -> bool | tuple[int, str]:
        # Check authorization
        if request.state.graph.is_authorized(request.state.actor, request.state.subject, mode):
            return True
        elif str(request.state.actor) == str(PUBLIC_ACTOR):
            return 401, "Unauthenticated actor"
        else:
            return 403, "Unauthorized"

    async def get(self, request: Request) -> JSONResponse:
        auth = self._check_auth(request, AccessMode.READ)
        if auth is not True:
            return JSONResponse({"error": auth[1]}, auth[0])

        # Retrieve the object identified by URI, passing actor for authorization
        doc = request.state.graph.activitystreams_cbd(
            request.state.subject, request.state.actor
        ).to_activitystreams(request.state.subject)

        if doc is None:
            return JSONResponse({"error": "Not found"}, 404)

        return JSONResponse(doc)

    async def post(self, request: Request) -> JSONResponse:
        auth = self._check_auth(request, AccessMode.WRITE)
        if auth is not True:
            return JSONResponse({"error": auth[1]}, auth[0])

        # POST target must be an inbox or outbox collection
        if not request.state.graph.is_a_box(request.state.actor):
            return JSONResponse({"error": "Not an inbox or outbox"}, 405)
