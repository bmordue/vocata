# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import rdflib

from .schema import AS, COLLECTION_TYPES, RDF


class ActivityPubCollectionsMixin:
    def collection_is_ordered(self, collection: str) -> bool:
        type_ = self.value(subject=collection, predicate=RDF.type)
        return type_ == AS.OrderedCollection

    def create_collection(self, collection: str, ordered: bool = False):
        collection = rdflib.URIRef(collection)
        if (collection, None, None) in self:
            raise TypeError(f"{collection} is already in graph")
        self._logger.debug("Adding%s collection at %s", " ordered" if ordered else "", collection)

        self.add((collection, RDF.type, AS.OrderedCollection if ordered else AS.Collection))
        self.add((collection, AS.totalItems, rdflib.Literal(0)))
        if ordered:
            items_node = rdflib.BNode()
            self.add((collection, AS.items, items_node))

    def add_to_collection(self, collection: str, item: str):
        if self.value(subject=collection, predicate=RDF.type) not in COLLECTION_TYPES:
            raise TypeError(f"{collection} is not a collection")
        # FIXME support pages
        if (collection, AS.items / (((RDF.rest * "*") / RDF.first) * "*"), item) in self:
            self._logger.debug("%s already in collection %s", item, collection)
            return
        self._logger.debug("Adding %s to collection %s", item, collection)

        total_items = self.value(subject=collection, predicate=AS.totalItems)
        if total_items is None:
            # FIXME start with correct count
            total_items = 0
        else:
            total_items = total_items.value
        total_items += 1
        self._logger.debug("New total items of %s: %d", collection, total_items)

        # FIXME support pages
        if self.collection_is_ordered(collection):
            rest = self.value(subject=collection, predicate=AS.items)
            items_node = rdflib.BNode()
            self.set((rdflib.URIRef(collection), AS.items, items_node))
            self.add((items_node, RDF.first, rdflib.URIRef(item)))
            if rest is not None:
                self.add((items_node, RDF.rest, rest))
        else:
            self.add((rdflib.URIRef(collection), AS.items, rdflib.URIRef(item)))
        self.set((rdflib.URIRef(collection), AS.totalItems, rdflib.Literal(total_items)))

    def remove_from_collection(self, collection: str, item: str):
        if self.value(subject=collection, predicate=RDF.type) not in COLLECTION_TYPES:
            raise TypeError(f"{collection} is not a collection")
        # FIXME support pages
        if (collection, AS.items / (((RDF.rest * "*") / RDF.first) * "*"), item) not in self:
            self._logger.debug("%s not in collection %s", item, collection)
            return
        self._logger.debug("Removing %s from collection %s", item, collection)

        total_items = self.value(subject=collection, predicate=AS.totalItems)
        if total_items is None:
            # FIXME start with coorect count
            total_items = 0
        else:
            total_items = total_items.value
        total_items -= 1
        self._logger.debug("New total items of %s: %d", collection, total_items)

        # FIXME support pages
        if self.collection_is_ordered(collection):
            seq_node = self.value(predicate=RDF.first, object=item)
            rest = self.value(subject=seq_node, predicate=RDF.rest)
            prev = self.value(predicate=AS.items | RDF.rest, object=seq_node)
            if rest:
                if prev == collection:
                    self.set((prev, AS.items, rest))
                else:
                    self.set((prev, RDF.rest, rest))
            else:
                if prev == collection:
                    self.remove((prev, AS.items, None))
                else:
                    self.remove((prev, RDF.rest, None))
            self.remove((seq_node, None, None))
        else:
            self.remove((rdflib.URIRef(collection), AS.items, rdflib.URIRef(item)))
        self.set((rdflib.URIRef(collection), AS.totalItems, rdflib.Literal(total_items)))
