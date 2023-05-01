+++
title = "Basic design"
description = "Basics to understand about the Vocata ActivityPub server"
weight = 10
sort_by = "weight"
template = "docs/page.html"

[extra]
toc = true
top = false
+++

## The social graph in Vocata

Assuming the [graph structure](../introduction/graph.md) of the [Fediverse], Vocata
uses [rdflib] to store its sub-graph. In contrast to other
[ActivityPub] servers, it does not derive its own data
structures from the objects it handles, but plainly
processes the graph operations defined by the protocol
to traverse and transform its sub-graph of the Fediverse.

## Notable differences from other ActivityPub servers

### Multi-domain / virtual hosting capability

Vocata can handle as many domains (URI [prefixes](prefixes.md)) as you want, by
simply making it reachable over HTTPS under the desired name (and flipping a
safety seitch).

This results mostly from Vocata's agnostic data structure – it simply handles
a [subgraph](../introduction/graph.md) of the Fediverse, without any need to
care about who authoritatively manages any part of it (if this sounds dangerous,
read more in the [security considerations](security.md)).

## Infrastructure of the server

The server is a Python ASGI application built on top of
[Starlette], using [Uvicorn] as ASGI server. For storing
the graph, it can use any SQL database supported by
[SQLAlchemy] (PostgreSQL and SQLite, but also MySQL/MariaDB
and some equally irrelevant databases).


[ActivityPub]: https://activitypub.rocks/
[Fediverse]: https://fediverse.party/
[rdflib]: https://rdflib.readthedocs.io/en/stable/
[Starlette]: https://www.starlette.io/
[Uvicorn]: https://www.uvicorn.org/
[SQLAlchemy]: https://www.sqlalchemy.org/
