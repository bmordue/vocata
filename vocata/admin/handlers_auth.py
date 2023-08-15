import os
from pathlib import Path
from starlette.routing import Route
from starlette.templating import Jinja2Templates
import logging

from starlette.responses import RedirectResponse
from starlette.authentication import SimpleUser

from starlette import status
from vocata.settings import get_settings
from vocata.graph.schema import AS
from . import auth


logger = logging.getLogger(__name__)

basepath = Path(__file__).parent

templates = Jinja2Templates(directory=basepath / "templates")

settings = get_settings(os.getenv("VOCATA_SETTINGS"))

SESSION_SECRET = settings.admin.session_secret_key


def hashed_account(account):
    return auth.hash_values(account, SESSION_SECRET)


class AdminUser(SimpleUser):
    def __init__(self, account, display_name):
        self.account = account
        self.display_name = display_name

    @property
    def identity(self) -> str:
        return str(self.actor)


async def check_auth(f, graph, templates, settings, request):
    logger.info("check_auth()")
    # check that session token has been set
    # and that there's a user

    # if no session, can't be logged in
    request.state.message = "Please login to access this site"

    if request.session is None:
        logger.error("check_auth - no session, returning login")
        return await handler_login(graph, templates, settings, request)

    ok, (account, session_token) = auth.check_session(request)

    if not ok:
        logger.error("check_auth - no session data, returning login")
        return RedirectResponse("/login")

    hashed_account = auth.hash_values(account, SESSION_SECRET)

    if not hashed_account == session_token:
        # extra layer of security on session spoofing
        auth.clean_session(request)
        logger.error("check_auth - bad session data, returning login")
        return RedirectResponse("/login")

    return await f(request)


async def handler_login(graph, templates, settings, request):
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
    if request.method == "GET":
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "servername": settings.admin.servername,
            },
        )

    form = await request.form()

    account = form.get("account")
    password = form.get("password")
    if not (account and password):
        logger.warning(f"No account ({account}) or no password")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "servername": settings.admin.servername,
                "message": "Account and Password required",
            },
        )

    verified = auth.verify_admin_login(graph, account, password)

    if verified:
        with graph:
            actor = graph.get_canonical_uri(f"acct:{account}")
            # get what we know about this user
            # but lets find a way to filter for certain useful predicates
            # so we don't pull keys, passwords, etc
            display_name = graph.value(actor, AS.name) or account

        user = AdminUser(account=account, display_name=display_name)
        request.state.user = user
        auth.setup_session(request, account, hashed_account(account))

        return templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": "/",
            },
        )

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "servername": settings.admin.servername,
            "account": account,
            "message": f"Could not login account {account}",
        },
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def handler_logout(graph, templates, settings, request):
    auth.clean_session(request)
    return RedirectResponse("/login")


routes = [
    Route("/login", endpoint=handler_login, methods=["GET", "POST"]),
    Route("/logout", endpoint=handler_login, methods=["GET"]),
]
