from .activitypub import ActivityPubGraph
from .authz import AccessMode
from .schema import VOC


def get_graph(database: str | None = None) -> ActivityPubGraph:
    graph = ActivityPubGraph("SQLAlchemy", identifier=str(VOC.Instance))
    if database is None:
        # FIXME Make configurable
        database = "sqlite:///graph.db"
    graph.open(database, create=True)

    return graph


__all__ = ["AccessMode", "ActivityPubGraph", "get_graph"]
