from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...data import AccessMode, PUBLIC_ACTOR, get_graph


class ActivityPubEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        graph = get_graph()

        actor = request.state.actor
        subject = str(request.url)

        # Check authorization
        if not graph.is_authorized(actor, subject, AccessMode.READ):
            if str(actor) == str(PUBLIC_ACTOR):
                return JSONResponse({"error": "Unauthenticated actor"}, 401)
            else:
                return JSONResponse({"error": "Unauthorized"}, 403)

        # Retrieve the object identified by URI, passing actor for authorization
        doc = graph.get_single_activitystream(subject, actor)

        if doc is None:
            return JSONResponse({"error": "Not found"}, 404)

        return JSONResponse(doc)

    async def post(self, request: Request) -> JSONResponse:
        graph = get_graph()

        actor = request.state.actor
        subject = str(request.url)

        # Check authorization
        if not graph.is_authorized(actor, subject, AccessMode.WRITE):
            if str(actor) == str(PUBLIC_ACTOR):
                return JSONResponse({"error": "Unauthenticated actor"}, 401)
            else:
                return JSONResponse({"error": "Unauthorized"}, 403)

        # POST target must be an inbox or outbox collection
        if not graph.is_a_box(actor):
            return JSONResponse({"error": "Not an inbox or outbox"}, 405)
