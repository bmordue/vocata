import rdflib

from .schema import AS, RDF


class ActivityPubCollectionsMixin:
    def add_to_collection(self, collection: str, item: str):
        self._logger.debug("Adding %s to collection %s", item, collection)

        type_ = self.value(subject=collection, predicate=RDF.type)
        if type_ == AS.Collection:
            items_pred = AS.items
        elif type_ == AS.OrderedCollection:
            items_pred = AS.orderedItems
        else:
            raise TypeError(f"{collection} is not a known collection type")
        self._logger.debug("%s is of type %s", collection, type_)

        total_items = self.value(subject=collection, predicate=AS.totalItems)
        if total_items is None:
            total_items = 0
        else:
            total_items = int(total_items)
        total_items += 1
        self._logger.debug("New total items of %s: %d", collection, total_items)

        # FIXME support pages
        self.add((rdflib.URIRef(collection), items_pred, rdflib.URIRef(item)))
        self.set((rdflib.URIRef(collection), AS.totalItems, rdflib.Literal(total_items)))
