import os
import pytest
from rdflib import RDF, Graph, Literal, URIRef

from vocata.graph import ActivityPubGraph
from vocata.graph.schema import AS
from vocata.server.app import app
from starlette.testclient import TestClient

_graph = None


@pytest.fixture(scope="module")
def graph():
    global _graph
    if _graph is None:
        _graph = ActivityPubGraph(database="sqlite:///:memory:")
    with _graph as graph:
        yield graph


@pytest.fixture()
def local_prefix(graph):
    graph.set_local_prefix("https://example.com")
    yield "https://example.com"
    for s, p, o in graph:
        if s.startswith("https://example.com") or o.startswith("https://example.com"):
            graph.remove((s, p, o))


@pytest.fixture()
def local_domain(local_prefix):
    return local_prefix.removeprefix("https://")


@pytest.fixture()
def local_actors(graph, local_domain):
    actors = []
    for i in range(3):
        actors.append(
            graph.create_actor_from_acct(
                f"pytest{i}@{local_domain}", f"Pytest Test Person {i}", "Person", force=False
            )
        )
    yield actors
    for actor in actors:
        graph.remove((actor, None, None))
        graph.remove((None, None, actor))


@pytest.fixture
def client():
    os.environ["VOC_GRAPH__DATABASE__STORE"] = "Memory"
    os.environ["VOC_GRAPH__DATABASE__URI"] = ""
    with TestClient(app, base_url="https://testserver") as client:
        graph = client.app_state["graph"]
        graph.set_local_prefix(str(client.base_url))
        yield client

@pytest.fixture
def app_graph(client):
    return client.app_state["graph"]


@pytest.fixture
def actor_iri(client: TestClient, app_graph: Graph) -> URIRef:
    acct_name = f"test@{client.base_url.netloc.decode()}"
    app_graph.create_actor_from_acct(acct_name, "Test Actor", "Person", False)
    return app_graph.value(predicate=RDF.type, object=AS.Person)


@pytest.fixture
def object_iri(note_iri: URIRef) -> URIRef:
    return note_iri


@pytest.fixture
def note_iri(client: TestClient, app_graph: Graph) -> URIRef:
    note_iri = URIRef(f"{client.base_url}/object-1")
    app_graph.set((note_iri, RDF.type, AS.Note))
    app_graph.set((note_iri, AS.content, Literal("TEST_CONTENT")))
    return note_iri

