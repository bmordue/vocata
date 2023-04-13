from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route

from ..graph import get_graph
from .activitypub import ActivityPubEndpoint
from .middleware import ActivityPubActorMiddleware
from .nodeinfo import NodeInfoEndpoint, nodeinfo_wellknown
from .webfinger import WebfingerEndpoint

middlewares = [Middleware(ActivityPubActorMiddleware)]
routes = [
    Mount(
        "/.well-known",
        routes=[
            Route("/nodeinfo", nodeinfo_wellknown, name="nodeinfo"),
            Route("/webfinger", WebfingerEndpoint, name="webfinger"),
        ],
        name="well_known",
    ),
    Mount(
        "/_functional",
        routes=[
            Route("/nodeinfo", NodeInfoEndpoint, name="nodeinfo"),
        ],
        name="functional",
    ),
    Route("/{path:path}", ActivityPubEndpoint, methods=["GET", "POST"]),
]

app = Starlette(debug=True, middleware=middlewares, routes=routes)
app.state.graph = get_graph()

__all__ = ["app"]
