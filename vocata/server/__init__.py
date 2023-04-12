from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route

from .endpoints.activitypub import ActivityPubEndpoint
from .endpoints.well_known import FUNCTIONAL, WELL_KNOWN
from .middleware import ActivityPubActorMiddleware

middlewares = [Middleware(ActivityPubActorMiddleware)]
routes = [
    Mount("/.well-known", routes=WELL_KNOWN, name="well_known"),
    Mount("/_functional", routes=FUNCTIONAL, name="functional"),
    Route("/{path:path}", ActivityPubEndpoint, methods=["GET", "POST"]),
]

app = Starlette(debug=True, middleware=middlewares, routes=routes)
