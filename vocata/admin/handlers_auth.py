import logging

from starlette import status
from starlette.responses import RedirectResponse
from starlette.routing import Route

from . import auth

logger = logging.getLogger(__name__)


async def handler_login(request):
    """
    Handle login page

    If GET:
        - show the login page, with optional message

    if POST:
        - account and password sent - no
            - back to login page with message
        - account and password sent - yes
            - verify account and password - yes
                - set session key and redir to dashboard
            - verify account and password - no
                - back to login page with message
    """
    app = request.app.state
    if request.method == "GET":
        return app.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "servername": app.settings.admin.servername,
            },
        )

    form = await request.form()

    account = form.get("account")
    password = form.get("password")
    if not (account and password):
        logger.warning(f"No account ({account}) or no password")
        return app.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "servername": app.settings.admin.servername,
                "message": "Account and Password required",
            },
        )

    verified = auth.verify_admin_login(app.graph, account, password)

    if verified:
        auth.setup_session(request, account, auth.hashed_account(account))

        return app.templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": "/",
            },
        )

    return app.templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "servername": app.settings.admin.servername,
            "account": account,
            "message": f"Could not login account {account}",
        },
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@auth.requires_auth
async def handler_logout(request):
    auth.clean_session(request)
    return RedirectResponse(request.url_for("login"))


routes = [
    Route("/login", name="login", endpoint=handler_login, methods=["GET", "POST"]),
    Route("/logout", name="logout", endpoint=handler_logout, methods=["GET"]),
]
