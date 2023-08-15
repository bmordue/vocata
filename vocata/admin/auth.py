import os
from enum import StrEnum
from hashlib import sha256
import logging
from functools import wraps
from starlette.responses import RedirectResponse
from starlette.authentication import SimpleUser

from vocata.settings import get_settings
from vocata.graph.schema import AS, VOC


settings = get_settings(os.getenv("VOCATA_SETTINGS"))

SESSION_TOKEN_KEY = "vocata-token"
SESSION_ACCOUNT_KEY = "vocata-account"

SESSION_SECRET = settings.admin.session_secret_key

logger = logging.getLogger(__name__)


class ActorSystemRole(StrEnum):
    admin = "admin"
    moderator = "moderator"
    member = "member"


class AdminUser(SimpleUser):
    def __init__(self, account, name, role=ActorSystemRole.member):
        self.account = account
        self.name = name
        self.role = role

    @property
    def identity(self) -> str:
        return str(self.actor)

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def acct(self):
        return f"acct:{self.account}"


def hash_values(*args):
    return sha256(("".join(args)).encode("utf-8")).hexdigest()


def hashed_account(account):
    return hash_values(account, SESSION_SECRET)


def verify_admin_login(graph, account, password) -> bool:
    logger.debug(f"verify_admin_login account: {account}")
    with graph:
        actor = graph.get_canonical_uri(f"acct:{account}")

        verified = graph.verify_actor_password(actor, password)
        logger.debug(f"Account {account} login verified? {verified}")

        if verified:
            logger.debug(f"Check account {account} permissions")
            # Poor man's ACL until we get ACLs
            if not graph.get_actor_role(actor) in [
                ActorSystemRole.admin,
                ActorSystemRole.moderator,
            ]:
                logger.warning(f"Account {account} denied, no admin access")
                verified = False

    logger.debug(f"Account {account} verified, login successful")
    return verified


def requires_auth(f):
    @wraps(f)
    async def check_auth(request):
        app = request.app.state
        logger.info("check_auth()")
        # check that session token has been set
        # and that there's a user

        # if no session, can't be logged in
        request.state.message = "Please login to access this site"
        if hasattr(request.state, "user"):
            return await f(request)

        if request.session is None:
            logger.error("check_auth - no session, returning login")
            return RedirectResponse(request.url_for("login"))

        ok, (account, session_token) = check_session(request)

        if not ok:
            logger.error("check_auth - no session data, returning login")
            return RedirectResponse(request.url_for("login"))

        hashed_account = hash_values(account, SESSION_SECRET)

        if not hashed_account == session_token:
            # extra layer of security on session spoofing
            clean_session(request)
            logger.error("check_auth - bad session data, returning login")
            return RedirectResponse(request.url_for("login"))

        with app.graph as graph:
            actor = graph.get_canonical_uri(f"acct:{account}")
            # get what we know about this user
            # but lets find a way to filter for certain useful predicates
            # so we don't pull keys, passwords, etc
            actor_name = graph.value(actor, AS.name) or account
            actor_role = graph.value(actor, VOC.hasSystemRole) or ActorSystemRole.member

        user = AdminUser(account=account, name=actor_name, role=actor_role)
        request.state.user = user

        return await f(request)

    return check_auth


def check_session(request):
    account = request.session.get(SESSION_ACCOUNT_KEY)
    session_token = request.session.get(SESSION_TOKEN_KEY)
    return (account and session_token), (account, session_token)


def setup_session(request, account, session_token):
    request.session[SESSION_ACCOUNT_KEY] = account
    request.session[SESSION_TOKEN_KEY] = session_token


def clean_session(request):
    del request.session[SESSION_ACCOUNT_KEY]
    del request.session[SESSION_TOKEN_KEY]
