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
from .schema import AS, RDF, VOC


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
    def __init__(
        self,
        store: str | None = None,
        *args,
        logger: logging.Logger | None = None,
        database: str | None = None,
        **kwargs,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._database = database
        if store is None:
            if self._database:
                self._store = "SQLAlchemy"
            else:
                self._store = "default"
        else:
            self._store = store

        super().__init__(self._store, *args, identifier=str(VOC.Instance), **kwargs)

    def __enter__(self):
        if self._database is not None:
            self.open(create=True)
        return self

    def __exit__(self, *args):
        if self._database is not None:
            self.close()

    def open(self, *args, **kwargs):
        self._logger.debug("Opening graph store from %s", self._database)
        super().open(self._database, *args, **kwargs)

        self.schema_migrate()

    def schema_migrate(self):
        self._logger.info("Migrating graph schema")
        # FIXME find better code structure;
        #  probably in conjunction with describing transformations in-graph

        # 2023-04-28 Use AS.alsoKnownAs on actor to link webfinger acct
        for s, p, o in self.triples((None, VOC.webfingerHref, None)):
            self._logger.debug("Replacing webfingerHref for %s with alsoKnownAs on %s", s, o)
            self.add((o, AS.alsoKnownAs, s))
            self.remove((s, p, o))

        # 2023-04-30 Local prefixes should be a Service actor
        for s in self.subjects(predicate=VOC.isLocal, object=rdflib.Literal(True), unique=True):
            if (s, RDF.type, AS.Service) not in self:
                from urllib.parse import urlparse

                domain = urlparse(str(s)).netloc
                self.create_actor(
                    s, AS.Service, username=domain, name=f"Vocata instance at {domain}", force=True
                )
                self.add((s, AS.alsoKnownAs, rdflib.URIRef(f"acct:{domain}@{domain}")))

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
