from enum import StrEnum
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)

SESSION_TOKEN_KEY = "vocata-token"
SESSION_ACCOUNT_KEY = "vocata-account"


class ActorSystemRole(StrEnum):
    admin = "admin"
    moderator = "moderator"
    member = "member"


def hash_values(*args):
    return sha256(("".join(args)).encode("utf-8")).hexdigest()


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


def check_session(request):
    account = request.session[SESSION_ACCOUNT_KEY]
    session_token = request.session[SESSION_TOKEN_KEY]
    return (account and session_token), (account, session_token)


def setup_session(request, account, session_token):
    request.session[SESSION_ACCOUNT_KEY] = account
    request.session[SESSION_TOKEN_KEY] = session_token


def clean_session(request):
    del request.session[SESSION_ACCOUNT_KEY]
    del request.session[SESSION_TOKEN_KEY]
