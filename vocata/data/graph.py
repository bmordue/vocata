import json

import rdflib
from pyld import jsonld

from .util import jsonld_single


class ActivityPubGraph(rdflib.Graph):
    def filter_subject(
        self, subject: rdflib.IdentifiedNode, recursive: bool = True
    ) -> "ActivityPubGraph":
        to_deref = {subject}
        seen = set()
        new_g = self.__class__()

        while to_deref:
            node = to_deref.pop()
            seen.add(node)

            for s, p, o in self.triples((node, None, None)):
                new_g.add((s, p, o))

                if isinstance(o, rdflib.IdentifiedNode) and o not in seen:
                    to_deref.add(o)

        return new_g

    def to_activitystreams(self) -> dict:
        profile = "https://www.w3.org/ns/activitystreams"

        doc = json.loads(self.serialize(format="json-ld"))

        framed = jsonld.frame(doc, profile, options={"embed": "@always"})
        compacted = jsonld.compact(framed, profile)

        return compacted

    def get_single_jsonld(self, uri: str) -> dict:
        doc = self.filter_subject(rdflib.URIRef(uri)).to_activitystreams()
        single = jsonld_single(doc, uri)

        return single
