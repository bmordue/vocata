# FIXME rename file

import logging
from typing import Iterator

import rdflib

from .activity import ActivityPubActivityMixin
from .actor import ActivityPubActorMixin
from .authz import ActivityPubAuthzMixin
from .collections import ActivityPubCollectionsMixin
from .federation import ActivityPubFederationMixin
from .jsonld import JSONLDMixin
from .prefix import ActivityPubPrefixMixin
from .schema import RDF


class ActivityPubGraph(
    rdflib.Graph,
    ActivityPubAuthzMixin,
    ActivityPubPrefixMixin,
    ActivityPubCollectionsMixin,
    ActivityPubActorMixin,
    ActivityPubActivityMixin,
    JSONLDMixin,
    ActivityPubFederationMixin,
):
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        super().__init__(*args, **kwargs)

    def open(self, database: str, *args, **kwargs):
        self._logger.debug("Opening graph store from %s", database)
        super().open(database, *args, **kwargs)

    def roots(self) -> Iterator[rdflib.term.Node]:
        # FIXME try upstreaming to rdflib
        for subject in self.subjects(unique=True):
            if (None, None, subject) not in self:
                yield subject

    def uri_subjects(
        self, prefix: str | None
    ) -> Iterator[tuple[rdflib.URIRef, rdflib.URIRef | None]]:
        if prefix is None:
            prefix = "https://"

        for s in self.subjects(unique=True):
            if not isinstance(s, rdflib.URIRef):
                continue
            if prefix and not s.startswith(prefix):
                continue

            type_ = self.value(subject=s, predicate=RDF.type)
            yield s, type_


__all__ = ["ActivityPubGraph"]
