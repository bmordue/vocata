# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from ..graph import ActivityPubGraph
from ..settings import get_settings
from .activitypub import ActivityPubEndpoint, ProxyEndpoint
from .metrics import MetricsEndpoint, RequestMetricsMiddleware, get_metrics_registry
from .middleware import ActivityPubActorMiddleware
from .nodeinfo import NodeInfoEndpoint, nodeinfo_wellknown
from .oauth import OAuthMetadataEndpoint
from .webfinger import WebfingerEndpoint
from .signin import AuthSigninEndpoint, AuthSignoutEndpoint
from .admin import main as admin



settings = get_settings()

BASE_UI_PATH = Path(__file__).parent / "web"
BASE_STATIC_PATH = BASE_UI_PATH / "static"
BASE_TEMPLATES_PATH = BASE_UI_PATH / "templates"

middlewares = [
    Middleware(ProxyHeadersMiddleware, trusted_hosts=settings.server.trusted_proxies),
    Middleware(SessionMiddleware, secret_key=settings.admin.session_secret_key),
    Middleware(RequestMetricsMiddleware),
    Middleware(ActivityPubActorMiddleware, pass_thru_paths=["/auth", "/static"]),
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
    Mount(
        "/auth",
        name="auth",
        routes=[
            Route("/signin", AuthSigninEndpoint, name="signin", methods=["GET", "POST"]),
            Route("/signout", AuthSignoutEndpoint, name="signout", methods=["GET"]),
        ],
    ),
    Mount("/admin", name="admin", routes=admin.routes),
    Mount("/static", StaticFiles(directory=BASE_STATIC_PATH), name="static"),
    Route("/{path:path}", ActivityPubEndpoint, methods=["GET", "POST"]),
]


@asynccontextmanager
async def _lifespan(app: Starlette) -> dict:
    settings = get_settings()

    templates = Jinja2Templates(BASE_TEMPLATES_PATH)

    # FIXME pass logger here
    with ActivityPubGraph(
        store=settings.graph.database.store, database=settings.graph.database.uri
    ) as graph, TemporaryDirectory() as metrics_tmp_dir:
        graph.fsck(fix=True)
        yield {
            "graph": graph,
            "metrics_registry": get_metrics_registry(metrics_tmp_dir),
            "used_prefixes": set(),
            "templates": templates,
        }


app = Starlette(middleware=middlewares, routes=routes, lifespan=_lifespan)

__all__ = ["app"]
