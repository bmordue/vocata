from dynaconf.base import LazySettings

from .activitypub import ActivityPubGraph
from .authz import AccessMode
from .schema import VOC


def get_graph(settings: LazySettings) -> ActivityPubGraph:
    graph = ActivityPubGraph("SQLAlchemy", identifier=str(VOC.Instance))
    graph.open(settings.graph.database.uri, create=True)

    return graph


__all__ = ["AccessMode", "ActivityPubGraph", "get_graph"]
