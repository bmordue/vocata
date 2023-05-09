import os
from contextlib import contextmanager
from urllib.parse import urlparse

import pytest
from rdflib import RDF, Graph, Literal, URIRef
from starlette.testclient import TestClient

from vocata.graph import ActivityPubGraph
from vocata.graph.schema import AS
from vocata.server.app import app

_graph = None

DEFAULT_PREFIX = "https://example.com"


@pytest.fixture(scope="module")
def graph():
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
def get_prefix(graph):
    @contextmanager
    def __get_prefix(prefix=DEFAULT_PREFIX):
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
def get_actors(graph, get_prefix):
    @contextmanager
    def __get_actors(n=3, prefix=DEFAULT_PREFIX):
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
def get_notes(graph, get_prefix):
    @contextmanager
    def __get_notes(n=3, prefix=DEFAULT_PREFIX):
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
def client():
    global _graph

    os.environ["VOC_GRAPH__DATABASE__STORE"] = "Memory"
    os.environ["VOC_GRAPH__DATABASE__URI"] = ""
    with TestClient(app, base_url="https://testserver") as client:
        _graph = client.app_state["graph"]
        yield client
