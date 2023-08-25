import typing as t
from urllib.parse import urlparse
from starlette.endpoints import HTTPEndpoint

from starlette.requests import Request
from starlette.responses import RedirectResponse

from starlette import status
from ..graph.authz import PUBLIC_ACTOR
from .middleware import DetermineActor
import logging

if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


def handle_signin_error(request, err):
    url = str(request.url_for("auth:signin")) + f"?error={err}"
    return request.state.templates.TemplateResponse(
        "redirect.html",
        {
            "request": request,
            "location": url,
        },
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


AUTH_ERROR = (
    "Could not authenticate user, please check your credentials "
    "and try again, or contact the administrator."
)


class AuthSigninEndpoint(HTTPEndpoint):
    def is_authenticated(self, request: Request):
        print(f"is_authenticated: {request.state.actor}")
        return hasattr(request.state, "actor") and request.state.actor is not PUBLIC_ACTOR

    async def get(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.debug(f"AuthSigninEndpoint.get {request.url.path}")

        # test if actor was already identified in the session
        if self.is_authenticated(request):
            return RedirectResponse(request.url_for("admin:dashboard"))

        return request.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Login",
            },
        )

    async def post(self, request) -> RedirectResponse:
        request.state.graph._logger.debug(f"AuthSigninEndpoint.post {request.url.path}")

        try:
            # check the form
            da = DetermineActor(required=True)
            actor = await da.from_form(request, required=True)
            request.state.actor = actor

            return request.state.templates.TemplateResponse(
                "redirect.html",
                {
                    "request": request,
                    "location": request.url_for("admin:dashboard"),
                },
            )
        except (KeyError, ValueError):
            return handle_signin_error(
                request,
                AUTH_ERROR,
            )


class AuthSignoutEndpoint(HTTPEndpoint):
    async def get(self, request) -> "TemplateResponse":
        # # https://stackoverflow.com/questions/68460918/starlette-session-state-clearing
        # clean session and return HTML redirect
        request.session.clear()
        # request.session[SESSION_KEY] = None
        request.session["logged_out"] = True

        return request.state.templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": request.url_for("auth:signin"),
            },
        )
