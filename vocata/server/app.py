from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from ..graph import ActivityPubGraph
from ..settings import get_settings
from .activitypub import ActivityPubEndpoint
from .middleware import ActivityPubActorMiddleware
from .nodeinfo import NodeInfoEndpoint, nodeinfo_wellknown
from .oauth import OAuthMetadataEndpoint
from .webfinger import WebfingerEndpoint

settings = get_settings()

middlewares = [
    Middleware(ProxyHeadersMiddleware, trusted_hosts=settings.server.trusted_proxies),
    Middleware(ActivityPubActorMiddleware),
]
routes = [
    Mount(
        "/.well-known",
        routes=[
            Route("/nodeinfo", nodeinfo_wellknown, name="nodeinfo"),
            Route("/oauth-authorization-server", OAuthMetadataEndpoint, name="oauth-metadata"),
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


@asynccontextmanager
async def _lifespan(app: Starlette) -> dict:
    settings = get_settings()

    # FIXME pass logger here
    with ActivityPubGraph(database=settings.graph.database.uri) as graph:
        yield {
            "graph": graph,
        }


app = Starlette(middleware=middlewares, routes=routes, lifespan=_lifespan)

__all__ = ["app"]
