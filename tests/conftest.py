import pytest

from vocata.graph import get_graph

_graph = None

@pytest.fixture(scope="module")
def graph():
    global _graph
    if _graph is None:
        _graph = get_graph(database="sqlite:///:memory:")
    return _graph

@pytest.fixture(scope="module")
def actor(graph):
    actor = graph.create_actor_from_acct("pytest1@example.com", "Pytest Test Person 1", "Person")

    return actor
