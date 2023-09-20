# SPDX-FileCopyrightText: © 2023 Steve Ivy <steve@monkinetic.blog>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from functools import wraps
from rdflib import URIRef

from starlette.responses import RedirectResponse
from starlette.authentication import SimpleUser


import logging

from ..graph.authz import PUBLIC_ACTOR, ActorSystemRole
from ..graph.activitypub import ActivityPubGraph
from ..graph.schema import AS, VOC

logger = logging.getLogger(__name__)


class APUser(SimpleUser):
    def __init__(self, actor: str | URIRef, name: str | None = None, role=None):
        self.actor = actor
        self.name = name or actor
        self.role = role

    @property
    def identity(self) -> str:
        return str(self.actor)

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def is_admin(self):
        return self.role == ActorSystemRole.admin

    @classmethod
    def load(cls, actor: str | URIRef, graph: ActivityPubGraph):
        obj = cls(actor=actor)
        with graph:
            obj.actor = actor
            obj.name = graph.value(actor, AS.name)
            obj.username = graph.value(actor, AS.preferredUsername)
            obj.role = graph.value(actor, VOC.hasServerRole)
            obj.avatar = graph.value(actor, AS.avatar)

        return obj


def requires_auth(f):
    @wraps(f)
    async def auth_user(self, request):
        request.state.graph._logger.info(f"auth_user() for {f.__name__}")
        # check that session token has been set
        # and that there's a user

        # if no session, can't be logged in
        if not hasattr(request.state, "actor"):
            request.state.graph._logger.info("no session?!? check middleware setup")
            return RedirectResponse(request.url_for("auth:signin"))

        if request.state.actor == PUBLIC_ACTOR:
            request.state.graph._logger.info("PUBLIC actor? whaaaa?")
            return RedirectResponse(request.url_for("auth:signin"))

        # add user to session/state for UI stuffs
        user = APUser.load(request.state.actor, request.state.graph)
        request.state.user = user

        return await f(self, request)

    return auth_user
