import pytest

from vocata.graph import ActivityPubGraph

_graph = None

@pytest.fixture(scope="module")
def graph():
    global _graph
    if _graph is None:
        _graph = ActivityPubGraph(database="sqlite:///:memory:")
    with _graph as graph:
        yield graph

@pytest.fixture(scope="module")
def local_prefix(graph):
    graph.set_local_prefix("https://example.com")
    return "https://example.com"

@pytest.fixture(scope="module")
def local_domain(local_prefix):
    return local_prefix.removeprefix("https://")

@pytest.fixture(scope="module")
def actor(graph, local_domain):
    actor = graph.create_actor_from_acct(f"pytest1@{local_domain}", "Pytest Test Person 1", "Person", force=False)

    return actor
