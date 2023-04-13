from .activitypub import ActivityPubGraph
from .authz import AccessMode
from .schema import VOC


def get_graph() -> ActivityPubGraph:
    graph = ActivityPubGraph("SQLAlchemy", identifier=str(VOC.Instance))
    # FIXME Make configurable
    graph.open("sqlite:///graph.db", create=True)

    # FIXME Remove
    from glob import glob
    import rdflib

    for f in glob("/home/nik/Privat/Vocata/test/*.json"):
        graph.parse(f, format="json-ld")
    graph.add(
        (
            rdflib.URIRef("acct:tester1@vocatadev.pagekite.me"),
            VOC.webfingerHref,
            rdflib.URIRef("https://vocatadev.pagekite.me/users/tester1"),
        )
    )

    return graph


__all__ = ["AccessMode", "ActivityPubGraph", "get_graph"]
