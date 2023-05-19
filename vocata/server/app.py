# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from ..graph import ActivityPubGraph
from ..settings import get_settings
from .activitypub import ActivityPubEndpoint, ProxyEndpoint
from .metrics import MetricsEndpoint, RequestMetricsMiddleware, get_metrics_registry
from .middleware import ActivityPubActorMiddleware
from .nodeinfo import NodeInfoEndpoint, nodeinfo_wellknown
from .oauth import OAuthMetadataEndpoint
from .webfinger import WebfingerEndpoint

settings = get_settings()

middlewares = [
    Middleware(ProxyHeadersMiddleware, trusted_hosts=settings.server.trusted_proxies),
    Middleware(RequestMetricsMiddleware),
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
            Route("/metrics", MetricsEndpoint, name="metrics"),
            Route("/nodeinfo", NodeInfoEndpoint, name="nodeinfo"),
            Route("/proxy", ProxyEndpoint, name="proxy", methods=["POST"]),
        ],
        name="functional",
    ),
    Route("/{path:path}", ActivityPubEndpoint, methods=["GET", "POST"]),
]


@asynccontextmanager
async def _lifespan(app: Starlette) -> dict:
    settings = get_settings()

    # FIXME pass logger here
    with ActivityPubGraph(
        store=settings.graph.database.store, database=settings.graph.database.uri
    ) as graph, TemporaryDirectory() as metrics_tmp_dir:
        graph.fsck(fix=True)
        yield {
            "graph": graph,
            "metrics_registry": get_metrics_registry(metrics_tmp_dir),
            "used_prefixes": set(),
        }


app = Starlette(middleware=middlewares, routes=routes, lifespan=_lifespan)

__all__ = ["app"]
