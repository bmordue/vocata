import typing as t
import rdflib
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request

from ..auth import requires_auth
from ...graph.activitypub import ActivityPubGraph
from ...graph.schema import VOC, AS

import logging

NAMESPACES = {
    "as": AS,
    "voc": VOC,
}


if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


class AdminUsersEndpoint(HTTPEndpoint):
    @requires_auth
    async def get(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.info("AdminDashboardEndpoint.get()")

        graph: ActivityPubGraph
        with request.state.graph as graph:
            users = list(graph.get_users())

        return request.state.templates.TemplateResponse(
            "admin/users.html",
            {
                "request": request,
                "users": users,
            },
        )


class AdminUserEndpoint(HTTPEndpoint):
    @requires_auth
    async def get(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.info("AdminUserEndpoint.get()")

        account = request.path_params["account"]

        graph: ActivityPubGraph
        with request.state.graph as graph:
            users = list(graph.get_user(account=account))
            user = users[0]
            actor = graph.value(predicate=AS.preferredUsername, object=rdflib.Literal(account))

        return request.state.templates.TemplateResponse(
            "admin/user-edit.html",
            {
                "request": request,
                "form_title": f"Edit User {account}",
                "actor": actor,
                "edituser": user,
            },
        )

    async def post(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.info("AdminUserEndpoint.post()")

        account = request.path_params["account"]

        form = await request.form()
        actor = form.get("actor")
        username = form["username"]

        if username != account:
            return request.state.templates.TemplateResponse(
                "redirect.html",
                {
                    "request": request,
                    "location": request.url_for("admin:users_edit", account=username),
                },
            )

        name = form["name"]
        email = form["email"]
        isadmin = form.get("account", "yes") == "yes"
        role = "admin" if isadmin else ""

        if actor:
            graph: ActivityPubGraph
            with request.state.graph as graph:
                userdata = {
                    "actor": rdflib.URIRef(actor),
                    "username": rdflib.Literal(username),
                    "name": rdflib.Literal(name),
                    "email": rdflib.Literal(email),
                    "role": rdflib.Literal(role),
                }

                graph.update_user(**userdata)

        return request.state.templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": request.url_for("admin:users_edit", account=username),
            },
        )
