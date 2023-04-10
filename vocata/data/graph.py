import json

import rdflib
from pyld import jsonld

from .util import jsonld_single, jsonld_cleanup_ids


class ActivityPubGraph(rdflib.Graph):
    def filter_subject(
        self,
        subject: rdflib.IdentifiedNode,
        recurse_bnodes: bool = True,
        recurse_uris: bool = False,
    ) -> "ActivityPubGraph":
        to_deref = {subject}
        seen = set()
        new_g = self.__class__()

        while to_deref:
            node = to_deref.pop()
            seen.add(node)

            for s, p, o in self.triples((node, None, None)):
                new_g.add((s, p, o))

                if o in seen:
                    continue
                if recurse_bnodes and isinstance(o, rdflib.BNode):
                    to_deref.add(o)
                elif not recurse_uris:
                    continue
                elif recurse_uris is True and isinstance(o, rdflib.URIRef):
                    to_deref.add(o)
                elif p in recurse_uris and isinstance(o, rdflib.URIRef):
                    to_deref.add(o)

        return new_g

    def to_activitystreams(self) -> dict:
        profile = "https://www.w3.org/ns/activitystreams"

        doc = json.loads(self.serialize(format="json-ld"))

        framed = jsonld.frame(doc, profile, options={"embed": "@always"})
        compacted = jsonld.compact(framed, profile)

        return compacted

    def get_single_activitystream(self, uri: str) -> dict:
        doc = self.filter_subject(rdflib.URIRef(uri)).to_activitystreams()
        single = jsonld_cleanup_ids(jsonld_single(doc, uri))

        return single
