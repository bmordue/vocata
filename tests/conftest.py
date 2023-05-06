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
