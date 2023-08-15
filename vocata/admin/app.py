import contextlib
import logging
import os
import typing as t
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from vocata.graph import ActivityPubGraph
from vocata.settings import get_settings

# from .handlers_settings import routes as settings_routes
from . import auth, handlers_auth, handlers_tools

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)s)",
)
logger = logging.getLogger(__name__)


basepath = Path(__file__).parent

settings = get_settings(os.getenv("VOCATA_SETTINGS"))
SESSION_SECRET = settings.admin.session_secret_key


async def healthcheck(request):
    return PlainTextResponse("OK")


@auth.requires_auth
async def dashboard(request):
    app = request.app.state
    return app.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "servername": settings.admin.servername,
        },
    )


middleware = [
    Middleware(SessionMiddleware, secret_key=SESSION_SECRET),
]


@contextlib.asynccontextmanager
async def lifespan(app):
    """
    Add the graph, templates object, and settings
    to the app object so that we can access them from
    just about anywhere.
    """
    app.state.graph = ActivityPubGraph(
        logger=logger,
        database=settings.graph.database.uri,
        store=settings.graph.database.store,
    )
    app.state.templates = Jinja2Templates(directory=basepath / "templates")
    app.state.settings = get_settings(os.getenv("VOCATA_SETTINGS"))

    yield


routes = [
    Route("/", name="dashboard", endpoint=dashboard, methods=["GET", "POST"]),
    Mount("/auth", routes=handlers_auth.routes),
    Mount("/advanced", routes=handlers_tools.routes),
    Route("/healthcheck", name="healthcheck", endpoint=healthcheck),
    # static files
    # swap out for CDN for "real" install
    Mount("/static", StaticFiles(directory=basepath / "static"), name="static"),
]

app = Starlette(debug=True, routes=routes, middleware=middleware, lifespan=lifespan)
