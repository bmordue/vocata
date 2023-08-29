import typing as t
import rdflib
from rdflib.plugins import sparql
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request

from ..auth import requires_auth
from ...graph.schema import VOC, AS, VCARD

import logging

NAMESPACES = {
    "as": AS,
    "voc": VOC,
    "vcard": VCARD,
}


if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)

users_query = """
SELECT ?name ?role ?username ?email ?isadmin
WHERE {
    ?actor a as:Person .
    ?actor as:name ?name .
    ?actor as:preferredUsername ?account .
    OPTIONAL {
        ?actor voc:hasServerRole ?role .
    }
    OPTIONAL {
        ?actor vcard:email ?email .
    }
    BIND (?account AS ?username)
    BIND ((?role = 'admin') as ?isadmin)
}
"""
users_query = sparql.prepareQuery(users_query, initNs=NAMESPACES)

user_query = """
SELECT ?name ?role ?username ?email ?isadmin
WHERE {
    ?actor a as:Person .
    ?actor as:name ?name .
    ?actor as:preferredUsername ?account .
    OPTIONAL {
        ?actor voc:hasServerRole ?role
    } .
    OPTIONAL {
        ?actor vcard:email ?email
    } .
    BIND (?account AS ?username)
    BIND ((?role = 'admin') as ?isadmin)
}
"""
user_query = sparql.prepareQuery(user_query, initNs=NAMESPACES)

insert_user_query = """
INSERT DATA {
    {actor} as:name {name} .
    {actor} as:preferredUsername {username} .
    {actor} voc:hasServerRole {role} .
    {actor} vcard:email {email} .
}"""


class AdminUsersEndpoint(HTTPEndpoint):
    @requires_auth
    async def get(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.info("AdminDashboardEndpoint.get()")

        with request.state.graph as graph:
            users = list(graph.query(users_query))

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

        with request.state.graph as graph:
            users = list(
                graph.query(
                    user_query,
                    initBindings={
                        "account": account,
                    },
                )
            )
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

        if not actor:
            print(f"No actor found for: {actor}")
        else:
            print(f"Saving data for actor {actor}")
            # print(insert_user_query.algebra)

            with request.state.graph as graph:
                userdata = {
                    "actor": rdflib.URIRef(actor),
                    "username": rdflib.Literal(username),
                    "name": rdflib.Literal(name),
                    "email": rdflib.Literal(email),
                    "role": rdflib.Literal(role),
                }
                print(f"updating user: {userdata}")
                insert_user_query = """
                PREFIX voc: <{voc_ns}>
                PREFIX as: <{as_ns}>
                PREFIX vcard: <{vcard_ns}>

                INSERT DATA {{
                    <{actor}> as:name '{name}' .
                    <{actor}> as:preferredUsername '{username}' .
                    <{actor}> voc:hasServerRole '{role}' .
                    <{actor}> vcard:email 'mailto:{email}' .
                }}""".format(
                    voc_ns=VOC,
                    as_ns=AS,
                    vcard_ns=VCARD,
                    **userdata,
                )
                print(insert_user_query)

                graph.update(
                    insert_user_query,
                    initBindings=userdata,
                )

        return request.state.templates.TemplateResponse(
            "redirect.html",
            {
                "request": request,
                "location": request.url_for("admin:users_edit", account=username),
            },
        )
