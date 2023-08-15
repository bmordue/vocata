# https://toot.cafe/@sivy/110866405869688502
from starlette.routing import Route
import logging
import rdflib

from . import utils, auth

logger = logging.getLogger(__name__)


@auth.requires_auth
async def handler_advanced_home(request):
    app = request.app.state
    return app.templates.TemplateResponse(
        "advanced/index.html",
        {
            "request": request,
        },
    )


@auth.requires_auth
async def handler_advanced_tools(request):
    app = request.app.state
    with app.graph as graph:
        actor = graph.get_canonical_uri(
            request.state.user.acct,
        )

    if request.method == "POST":
        form = await request.form()
        action: str = form.get("action")
        value: str = form.get("value")
        data = None
        error: str = ""

        if action == "pull" and value:
            logger.info(f"Pulling data for object {value}")
            with app.graph as graph:
                success, resp = graph.pull(value, actor)
                value_uri = graph.get_canonical_uri(value)

            if not success:
                logger.error(resp.content)
                logger.error(resp.headers)
                error = resp.json()["error"]

            data = None
            if success and value_uri:
                logger.info(f"Loading known data for object {value_uri}")
                with app.graph as graph:
                    data = utils.get_properties(graph, value_uri)
                    data = [(p.fragment, v) for p, v in data.items()]

        return app.templates.TemplateResponse(
            "advanced/tools.html",
            {
                "request": request,
                "servername": app.settings.admin.servername,
                "settings": app.settings,
                "action": action,
                f"{action}_value": value,
                f"{action}_data": data,
                "error": error,
            },
        )

    action = request.query_params.get("action")
    value = request.query_params.get("value")
    data = None
    if action == "view" and value:
        logger.info(f"Loading known data for object {value}")

        search_value = rdflib.URIRef(value)
        with app.graph as graph:
            data = utils.get_properties(graph, search_value)
        data = [(p.fragment, v) for p, v in data.items()]

    return app.templates.TemplateResponse(
        "advanced/tools.html",
        {
            "request": request,
            "servername": app.settings.admin.servername,
            "settings": app.settings,
            f"{action}_value": value,
            f"{action}_data": data,
        },
    )


routes = [
    Route("/", name="advanced", endpoint=handler_advanced_home, methods=["GET"]),
    Route(
        "/tools", name="advanced_tools", endpoint=handler_advanced_tools, methods=["GET", "POST"]
    ),
]
