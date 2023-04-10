from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..data import get_graph


class ActivityPubEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        graph = get_graph()

        # Retrieve the object identified by URI, passing actor for authorization
        doc = graph.get_single_activitystream(str(request.url), request.state.actor)

        if doc is None:
            return JSONResponse({"error": "Not found"}, 404)

        return JSONResponse(doc)
