# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

# FIXME rename file

import logging
from typing import Iterator

import rdflib

from .activity import ActivityPubActivityMixin
from .actor import ActivityPubActorMixin
from .authz import ActivityPubAuthzMixin
from .collections import ActivityPubCollectionsMixin
from .federation import ActivityPubFederationMixin
from .fsck import GraphFsckMixin
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
    GraphFsckMixin,
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

    def get_canonical_uri(self, uri: str) -> str | None:
        uri = rdflib.URIRef(uri)
        if (uri, RDF.type, None) in self:
            return uri

        uri = self.value(predicate=AS.alsoKnownAs, object=uri)
        if uri is not None:
            return uri

        return None


__all__ = ["ActivityPubGraph"]
