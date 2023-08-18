import typing as t
from urllib.parse import urlparse
from starlette.endpoints import HTTPEndpoint

# from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette import status

import logging

from vocata.graph.authz import AccessMode

if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


def handle_signin_error(request, err):
    return RedirectResponse(
        str(request.url_for("signin")) + "?error={err}",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


class AuthSigninEndpoint(HTTPEndpoint):
    def is_authenticated(self, request):
        return hasattr(request.state, "actor") and request.state.actor

    async def get(self, request) -> "TemplateResponse":
        # test if actor was already identified in the session
        if self.is_authenticated(request):
            uri = request.url_for("admin:dashboard")
            # protect against being redirected off
            # vocata
            target = request.query_params.get("t")
            if target:
                potential_uri = urlparse(t)
                with request.state.graph as graph:
                    p = graph.get_url_prefix(potential_uri)
                    if graph.is_local_prefix(p):
                        uri = potential_uri

            return RedirectResponse(uri)

        return request.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "target": request.query_params.get("t"),
            },
        )

    async def post(self, request) -> RedirectResponse:
        # process auth login
        logger.info("Signin request")
        if self.is_authenticated(request):
            return request.state.templates.TemplateResponse(
                "redirect.html",
                {
                    "request": request,
                    "location": request.url_for("admin:dashboard"),
                },
            )
        else:
            handle_signin_error(
                request,
                "Could not authenticate user, please check your credentials "
                "and try again, or contact the administrator.",
            )


class AuthSignoutEndpoint(HTTPEndpoint):
    async def get(self, request) -> "TemplateResponse":
        # clean session and return HTML direct

        return request.state.templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": request.url_for("signin"),
            },
        )
