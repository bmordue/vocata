# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import os
from contextlib import contextmanager
from typing import Callable, Generator
from urllib.parse import urlparse

import pytest
from rdflib import RDF, Literal, URIRef
from starlette.testclient import TestClient

from vocata.graph import ActivityPubGraph
from vocata.graph.schema import AS
from vocata.server.app import app

_graph: ActivityPubGraph | None = None

DEFAULT_PREFIX = "https://example.com"


@pytest.fixture(scope="module")
def graph() -> ActivityPubGraph:
    global _graph
    if _graph is None:
        graph_existed = False
        _graph = ActivityPubGraph(store="Memory", database="")
    else:
        graph_existed = True
    with _graph as graph:
        yield graph
    if not graph_existed:
        _graph = None


@pytest.fixture()
def get_prefix(
    graph: ActivityPubGraph,
) -> Callable[[str | None], Generator[tuple[str, str], None, None]]:
    @contextmanager
    def __get_prefix(prefix: str | None = DEFAULT_PREFIX) -> Generator[tuple[str, str], None, None]:
        prefix = str(prefix)
        if not graph.is_local_prefix(URIRef(prefix)):
            graph.set_local_prefix(prefix)

        try:
            yield prefix, urlparse(prefix).netloc
        finally:
            for s, p, o in graph:
                if s.startswith(prefix) or o.startswith(prefix):
                    graph.remove((s, p, o))

    return __get_prefix


@pytest.fixture()
def get_actors(
    graph: ActivityPubGraph,
    get_prefix: Callable[[str | None], Generator[tuple[str, str], None, None]],
) -> Callable[[int | None, str | None], Generator[list[URIRef], None, None]]:
    @contextmanager
    def __get_actors(
        n: int | None = 3, prefix: str | None = DEFAULT_PREFIX
    ) -> Generator[list[URIRef], None, None]:
        with get_prefix(prefix) as (prefix, domain):
            actors = []
            for i in range(n):
                actors.append(
                    graph.create_actor_from_acct(
                        f"pytest{i}@{domain}", f"Pytest Test Person {i}", "Person", force=False
                    )
                )
            yield actors
            for actor in actors:
                graph.remove((actor, None, None))
                graph.remove((None, None, actor))

    return __get_actors


@pytest.fixture()
def get_notes(
    graph: ActivityPubGraph,
    get_prefix: Callable[[str | None], Generator[tuple[str, str], None, None]],
) -> Callable[[int | None, str | None], Generator[list[URIRef], None, None]]:
    @contextmanager
    def __get_notes(
        n: int | None = 3, prefix: str | None = DEFAULT_PREFIX
    ) -> Generator[list[URIRef], None, None]:
        with get_prefix(prefix) as (prefix, domain):
            notes = []
            for i in range(n):
                note_iri = URIRef(f"{prefix}/object-{i}")
                graph.set((note_iri, RDF.type, AS.Note))
                graph.set((note_iri, AS.content, Literal("TEST_CONTENT {i}")))
                notes.append(note_iri)
            yield notes
            for note_iri in notes:
                graph.remove((note_iri, None, None))
                graph.remove((None, None, note_iri))

    return __get_notes


@pytest.fixture(scope="module")
def client() -> TestClient:
    global _graph

    os.environ["VOC_GRAPH__DATABASE__STORE"] = "Memory"
    os.environ["VOC_GRAPH__DATABASE__URI"] = ""
    with TestClient(app, base_url="https://testserver") as client:
        _graph = client.app_state["graph"]
        yield client
