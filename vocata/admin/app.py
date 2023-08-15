import typing as t
import os
from pathlib import Path
from functools import partial
import logging

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

# from starlette.middleware import Middleware
from starlette.routing import Mount, Route, Router
from starlette.templating import Jinja2Templates

from vocata.settings import get_settings

# from .handlers_settings import routes as settings_routes
# from .handlers_tools import routes as tools_routes
from .handlers_auth import routes as auth_routes, check_auth

from . import utils

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from dynaconf.base import LazySettings
    from vocata.graph import ActivityPubGraph


basepath = Path(__file__).parent

templates = Jinja2Templates(directory=basepath / "templates")

settings = get_settings(os.getenv("VOCATA_SETTINGS"))


SESSION_SECRET = settings.admin.session_secret_key


async def healthcheck(request):
    return PlainTextResponse("OK")


async def dashboard(graph, templates, settings, request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "servername": settings.admin.servername,
        },
    )


def add_handler(
    func_or_route: t.Union[t.Callable, Route],
    auth_required=False,
):
    settings: "LazySettings" = get_settings(os.getenv("VOCATA_SETTINGS"))
    templates: "Jinja2Templates" = Jinja2Templates(
        directory=basepath / "templates",
    )
    graph: "ActivityPubGraph" = utils.get_graph(logger, settings)

    if isinstance(func_or_route, Route):
        func = partial(func_or_route.endpoint, graph, templates, settings)
        func_or_route.endpoint = func
    else:
        func_or_route = partial(func_or_route, graph, templates, settings)

    if auth_required:
        func_or_route = partial(check_auth, func_or_route, graph, templates, settings)

    return func_or_route


middleware = [
    Middleware(SessionMiddleware, secret_key=SESSION_SECRET),
]

routes = [
    Route("/", endpoint=add_handler(dashboard, auth_required=True), methods=["GET", "POST"]),
    Mount("/auth", Router([add_handler(r, auth_required=True) for r in auth_routes])),
    Mount("/static", StaticFiles(directory=basepath / "static")),
]

app = Starlette(debug=True, routes=routes, middleware=middleware)
