import logging

# import rdflib
# from collections import defaultdict

from vocata.graph import ActivityPubGraph
from vocata.graph.schema import VOC

logger = logging.getLogger(__name__)

PREFIX_PROPERTIES = ["isLocal", "name", "preferredUsername"]


def get_graph(logger, settings):
    return ActivityPubGraph(
        logger=logger,
        database=settings.graph.database.uri,
        store=settings.graph.database.store,
    )


def get_prefixes(graph):
    data = {}
    with graph:
        for s, _, _ in graph.triples((None, VOC.isLocal, None)):
            data[s] = {}
            for _, p, o in graph.triples((s, None, None)):
                if p.fragment in PREFIX_PROPERTIES:
                    data[s][p.fragment] = o

    return data


def get_properties(graph, s):
    logger.debug("Get properties for %r" % s)
    with graph:
        t = list(graph.triples((s, None, None)))

        data = {}

        for s, p, o in t:
            logger.debug(f"Found {p} for %r: {o}" % s)
            data[p] = o

    return data
