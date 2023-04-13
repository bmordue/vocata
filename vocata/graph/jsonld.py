import json
from typing import Self

import rdflib
from pyld import jsonld
from rdflib.parser import PythonInputSource

from .schema import AS_URI


def jsonld_single(doc: dict, id_: str, key_: str = "id") -> dict:
    if "@graph" not in doc:
        if doc.get(key_) == id_:
            return doc
        raise KeyError(f"Input is a single object, but is not {id_}")

    new_doc = {}

    if "@context" in doc:
        new_doc["@context"] = doc["@context"]

    found = False
    for obj in doc["@graph"]:
        if obj[key_] == id_:
            new_doc.update(obj)
            found = True
            break

    if not found:
        raise KeyError(f"{id_} not found in graph")

    return new_doc


def jsonld_cleanup_ids(doc: dict, key_: str = "id", flatten: bool = True) -> dict:
    new_doc = {}
    for attr, value in doc.items():
        if isinstance(value, list):
            new_list = []
            for elem in value:
                if isinstance(elem, dict):
                    new_elem = jsonld_cleanup_ids(elem, key_)
                    if new_elem:
                        new_list.append(new_elem)
                else:
                    new_list.append(elem)
        elif isinstance(value, dict):
            new_value = jsonld_cleanup_ids(value, key_)
            if new_value:
                new_doc[attr] = new_value
        elif attr != key_ or not value.startswith("_:"):
            new_doc[attr] = value

    if flatten and len(new_doc) == 1 and key_ in new_doc:
        return new_doc[key_]

    return new_doc


class JSONLDMixin:
    def to_jsonld(self, profile) -> dict:
        doc = json.loads(self.serialize(format="json-ld"))

        framed = jsonld.frame(doc, profile, options={"embed": "@always"})
        compacted = jsonld.compact(framed, profile)

        return compacted

    def to_activitystream(self, uri: str | None = None) -> dict:
        doc = self.to_jsonld(AS_URI.removesuffix("#"))
        if uri:
            try:
                doc = jsonld_cleanup_ids(jsonld_single(doc, uri))
            except KeyError:
                doc = None
        return doc

    def activitystream_cbd(self, uri: str, actor: str) -> Self:
        self._logger.debug("Deriving CBD for %s as %s", uri, actor)
        cbd = self.__class__()
        subjects = {rdflib.URIRef(uri)}
        seen = set()
        while subjects:
            current_subject = subjects.pop()
            self._logger.debug("Adding %s to CBD", current_subject)
            seen.add(current_subject)
            new_cbd = self.cbd(current_subject, target_graph=self.__class__())
            for s, p, o in new_cbd.triples((None, None, None)):
                # We need to include objects with URI fragments,
                #  they cannot be dereferenced remotely alone
                if (
                    isinstance(o, rdflib.URIRef)
                    and o.fragment
                    and o not in seen
                    and o.startswith(s.removesuffix("#" + s.fragment) + "#")
                ):
                    subjects.add(o)
            cbd += new_cbd
        return cbd.filter_authorized(actor, self)

    def add_jsonld(self, data: dict) -> rdflib.Graph:
        # Parse into a new graph first, in case something fails
        new_g = rdflib.Graph()
        source = PythonInputSource(data, data["id"])
        new_g.parse(source, format="json-ld")

        # Remvoe all statements about subject and add new
        self._logger.debug("Replacing %s from JSON-LD document", data["id"])
        self.remove((data["id"], None, None))
        self += new_g

        return new_g


__all__ = ["JSONLDMixin"]
