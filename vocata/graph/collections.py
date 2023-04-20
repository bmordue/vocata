import rdflib

from .schema import AS, RDF


class ActivityPubCollectionsMixin:
    def get_collection_items_pred(self, collection: str) -> rdflib.URIRef:
        type_ = self.value(subject=collection, predicate=RDF.type)
        if type_ == AS.Collection:
            items_pred = AS.items
        elif type_ == AS.OrderedCollection:
            items_pred = AS.orderedItems
        else:
            raise TypeError(f"{collection} is not a known collection type")

        self._logger.debug("%s is of type %s", collection, type_)
        return items_pred

    def add_to_collection(self, collection: str, item: str):
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
        self.add((rdflib.URIRef(collection), items_pred, rdflib.URIRef(item)))
        self.set((rdflib.URIRef(collection), AS.totalItems, rdflib.Literal(total_items)))

    def remove_from_collection(self, collection: str, item: str):
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
        self.remove((rdflib.URIRef(collection), items_pred, rdflib.URIRef(item)))
        self.set((rdflib.URIRef(collection), AS.totalItems, rdflib.Literal(total_items)))
