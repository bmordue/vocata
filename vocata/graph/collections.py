# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import rdflib

from ..util.types import coerce_uris
from .schema import AS, RDF


class ActivityPubCollectionsMixin:
    @coerce_uris
    def get_collection_items_pred(self, collection: rdflib.URIRef) -> rdflib.URIRef:
        type_ = self.value(subject=collection, predicate=RDF.type)
        if type_ == AS.Collection:
            items_pred = AS.items
        elif type_ == AS.OrderedCollection:
            items_pred = AS.orderedItems
        else:
            raise TypeError(f"{collection} is not a known collection type")

        self._logger.debug("%s is of type %s", collection, type_)
        return items_pred

    @coerce_uris
    def add_to_collection(self, collection: rdflib.URIRef, item: rdflib.URIRef):
        self._logger.debug("Adding %s to collection %s", item, collection)

        items_pred = self.get_collection_items_pred(collection)

        total_items = self.value(subject=collection, predicate=AS.totalItems)
        if total_items is None:
            # FIXME start with correct count
            total_items = 0
        else:
            total_items = total_items.value
        total_items += 1
        self._logger.debug("New total items of %s: %d", collection, total_items)

        # FIXME support pages
        self.add((collection, items_pred, item))
        self.set((collection, AS.totalItems, total_items))

    @coerce_uris
    def remove_from_collection(self, collection: rdflib.URIRef, item: rdflib.URIRef):
        self._logger.debug("Removing %s from collection %s", item, collection)

        items_pred = self.get_collection_items_pred(collection)

        total_items = self.value(subject=collection, predicate=AS.totalItems)
        if total_items is None:
            # FIXME start with coorect count
            total_items = 0
        else:
            total_items = total_items.value
        total_items -= 1
        self._logger.debug("New total items of %s: %d", collection, total_items)

        # FIXME support pages
        self.remove((collection, items_pred, item))
        self.set((collection, AS.totalItems, total_items))
