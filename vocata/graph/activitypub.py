# FIXME rename file

import logging
from typing import Iterator
from uuid import uuid4

import rdflib

from .activity import ActivityPubActivityMixin
from .actor import ActivityPubActorMixin
from .authz import ActivityPubAuthzMixin
from .collections import ActivityPubCollectionsMixin
from .federation import ActivityPubFederationMixin
from .jsonld import JSONLDMixin
from .prefix import ActivityPubPrefixMixin
from .schema import RDF, VOC


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
        self.setup_instance()

    def setup_instance(self):
        if not self.instance_ref:
            self._logger.debug("Generating new instance ref")
            uuid = str(uuid4())
            ref = rdflib.URIRef(f"urn:uuid:{uuid}")

            self.add((VOC.Instance, VOC.instance, ref))
            self.add((ref, RDF.type, VOC.Instance))
        self._logger.debug("Instance ref is %s", self.instance_uuid)

    @property
    def instance_ref(self) -> rdflib.URIRef | None:
        return self.value(VOC.Instance, VOC.instance)

    @property
    def instance_uuid(self) -> str | None:
        ref = self.instance_ref
        if ref is None:
            return None
        return str(self.instance_ref).split(":")[2]

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
