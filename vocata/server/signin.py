import typing as t
from starlette.endpoints import HTTPEndpoint

# from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette import status

import logging

if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


def handle_signin_error(request, err):
    return RedirectResponse(
        request.url_for("signin") + f"?error={err}", status_code=status.HTTP_401_UNAUTHORIZED
    )


class AuthSigninEndpoint(HTTPEndpoint):
    async def get(self, request) -> "TemplateResponse":
        # show login.html
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

        form = await request.form()
        account = form.get("account")
        password = form.get("password")

        unauthed = handle_signin_error(
            request,
            "Could not authenticate user, please check your credentials "
            "and try again, or contact the administrator.",
        )

        if not account and password:
            return unauthed

        with request.state.graph as graph:
            actor = graph.get_canonical_uri(f"acct:{account}")
            if not graph.verify_actor_password(actor, password):
                return unauthed

            # FIXME: use graph.is_authorized() but new
            # AccessModes and/or actors needed
            if not request.self.graph.get_actor_role(actor) == "admin":
                return unauthed

        return RedirectResponse(
            request.url_for("admin.dashboard"),
        )


class AuthSignoutEndpoint(HTTPEndpoint):
    async def get(self, request) -> "TemplateResponse":
        # clean session and return HTML direct

        return request.state.templates.TemplateRespponse(
            "redirect.html",
            {
                "request": request,
                "location": request.url_for("signin"),
            },
        )
