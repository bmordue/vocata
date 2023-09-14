import typing as t

import rdflib
from rdflib.plugins import sparql
from ..graph.schema import VOC, AS, VCARD

NAMESPACES = {
    "as": AS,
    "voc": VOC,
    "vcard": VCARD,
}

SP_GET_USERS = """
SELECT ?actor ?name ?role ?username ?email ?isadmin ?localdomain ?actorPrefix
WHERE {
    ?actor a as:Person ;
           as:name ?name ;
           as:preferredUsername ?account .
    OPTIONAL {
        ?actor voc:hasServerRole ?role
    } .
    OPTIONAL {
        ?actor vcard:email ?email
    } .
    BIND (
        STRBEFORE(STRAFTER(str(?actor), '://'), '/') as ?localdomain
    )
    BIND (?account AS ?username)
    BIND ((?role = 'admin') AS ?isadmin)
    BIND (CONCAT(
        STRBEFORE(STR(?actor), "://"),
        "://") AS ?webSchema)
    BIND (STRAFTER(
        STR(?actor),
        ?webSchema) AS ?afterWebSchema)
    BIND (STRBEFORE(
        ?afterWebSchema,
        "/") AS ?actorDomain)
    BIND (CONCAT(
        ?webSchema,
        ?actorDomain) AS ?actorPrefix)
}
"""
SP_USERS_QUERY = sparql.prepareQuery(SP_GET_USERS, initNs=NAMESPACES)

SP_GET_USER = """
SELECT ?actor ?name ?role ?username ?email ?isadmin ?localdomain
WHERE {
    ?actor a as:Person ;
           as:name ?name ;
           as:preferredUsername ?account .
    OPTIONAL {
        ?actor voc:hasServerRole ?role
    } .
    OPTIONAL {
        ?actor vcard:email ?email
    } .
    BIND (
        STRBEFORE(STRAFTER(str(?actor), '://'), '/') as ?localdomain
    )
    BIND ((?role = 'admin') as ?isadmin)
    BIND (?account AS ?username)
}
"""
SP_USER_QUERY = sparql.prepareQuery(SP_GET_USER, initNs=NAMESPACES)

# FIXME: only returns prefixes with users?
#        make sure returns prefixes with 0 for prefix_users
#        if no users
# FIXME: This would be WAY simpler if we stored a property
# voc:hasPrefix for actors; then it just becomes:
#  `OPTIONAL { ?actor voc:hasPrefix ?prefix } .`
SP_GET_PREFIX_DATA = """
SELECT
    ?prefix
    ?domain
    ?isLocal
    (COUNT(?actor) AS ?prefixUsers)
WHERE {
    ?prefix a as:Service;
            as:preferredUsername ?domain .
    ?actor a as:Person .
    OPTIONAL {
        ?prefix voc:isLocal ?isLocal
    } .
    BIND (CONCAT(
        STRBEFORE(STR(?actor), "://"),
        "://") AS ?webSchema)
    BIND (STRAFTER(
        STR(?actor),
        ?webSchema) AS ?afterWebSchema)
    BIND (STRBEFORE(
        ?afterWebSchema,
        "/") AS ?actorDomain)
    BIND (CONCAT(
        ?webSchema,
        ?actorDomain) AS ?actorPrefix)
    FILTER (?prefix = IRI(?actorPrefix))
}
GROUP BY ?prefix
"""
SP_PREFIX_DATA_QUERY = sparql.prepareQuery(SP_GET_PREFIX_DATA, initNs=NAMESPACES)


class ActivityPubAdminMixin:
    def get_users(self) -> t.List:
        return list(self.query(SP_USERS_QUERY))

    def get_user(self, **bindings):
        users = list(
            self.query(
                SP_USER_QUERY,
                initBindings=bindings,
            )
        )
        if not users:
            return None

        user = users[0]
        return user

    def update_user(self, actor: str | rdflib.URIRef, **kwargs):
        if isinstance(actor, str):
            actor = rdflib.URIRef(actor)

        if name := kwargs.get("name"):
            self.set((actor, AS.name, rdflib.Literal(name)))

        if username := kwargs.get("username"):
            self.set((actor, AS.preferredUsername, rdflib.Literal(username)))

        role = kwargs.get("role", "")
        self.set((actor, VOC.hasServerRole, rdflib.Literal(role)))

        if email := kwargs.get("email"):
            email = email.removeprefix("mailto:")
            self.set((actor, VCARD.email, rdflib.Literal(f"mailto:{email}")))

    # prefix data
    def get_prefixes(self):
        prefix_data = list(
            self.query(
                SP_PREFIX_DATA_QUERY,
                initBindings={},
            )
        )
        return list(prefix_data)

    def sparql(self, squery, **bindings):
        query = sparql.prepareQuery(squery, initNs=NAMESPACES)
        res = self.query(query, initBindings=bindings)
        return list(res)
