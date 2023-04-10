from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from .endpoint import ActivityPubEndpoint
from .middleware import ActivityPubActorMiddleware

middlewares = [Middleware(ActivityPubActorMiddleware)]
routes = [Route("/{path:path}", ActivityPubEndpoint, methods=["GET", "POST"])]

app = Starlette(debug=True, middleware=middlewares, routes=routes)
