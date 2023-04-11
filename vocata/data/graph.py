import json
from uuid import uuid4

import rdflib
from pyld import jsonld
from rdflib.namespace import NamespaceManager, RDF

from .util import jsonld_single, jsonld_cleanup_ids

AS_URI = "https://www.w3.org/ns/activitystreams#"
AS = rdflib.Namespace(AS_URI)

VOC_URI = "https://docs.vocata.one/information-schema#"
VOC = rdflib.Namespace(VOC_URI)

LDP_URI = "http://www.w3.org/ns/ldp#"
LDP = rdflib.Namespace(LDP_URI)

AUDIENCE_PREDICATES = {AS.to, AS.bto, AS.cc, AS.bcc}


class ActivityPubGraph(rdflib.Graph):
    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        self.setup_instance()

    def setup_instance(self):
        if not self.instance_ref:
            uuid = str(uuid4())
            ref = rdflib.URIRef(f"urn:uuid:{uuid}")

            self.add((VOC.Instance, VOC.instance, ref))
            self.add((ref, RDF.type, VOC.Instance))

    @property
    def instance_ref(self) -> rdflib.URIRef | None:
        return self.value(VOC.Instance, VOC.instance)

    @property
    def instance_uuid(self) -> str | None:
        ref = self.instance_ref
        if ref is None:
            return None
        return str(self.instance_ref).split(":")[2]

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

    def is_a_box(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, LDP.inbox | AS.outbox, subject) in self

    def is_an_actor(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, AS.actor, subject) in self

    def is_public(self, subject: rdflib.term.Identifier | str) -> bool:
        predicates = set(self.predicates(subject=subject, object=AS.Public))
        return predicates & AUDIENCE_PREDICATES

    def is_authorized(self, actor: rdflib.URIRef | str | None, subject: rdflib.term.Identifier | str) -> bool:
        if self.is_public(subject):
            return True
        if self.is_an_actor(subject):
            return True

        return False

    def filter_authorized(
        self, actor: rdflib.URIRef | str | None, root_graph: rdflib.Graph | None = None
    ) -> rdflib.Graph:
        if root_graph is None:
            root_graph = self

        new_g = self.__class__()

        for subject in self.subjects():
            if root_graph.is_authorized(actor, subject):
                for s, p, o in self.triples((subject, None, None)):
                    new_g.add((s, p, o))

        return new_g

    def to_activitystreams(self) -> dict:
        profile = AS_URI

        doc = json.loads(self.serialize(format="json-ld"))

        framed = jsonld.frame(doc, profile, options={"embed": "@always"})
        compacted = jsonld.compact(framed, profile)

        return compacted

    def get_single_activitystream(self, uri: str, actor: str | None = None) -> dict | None:
        doc = (
            self.filter_subject(rdflib.URIRef(uri))
            .filter_authorized(actor, self)
            .to_activitystreams()
        )
        try:
            single = jsonld_cleanup_ids(jsonld_single(doc, uri))
        except KeyError:
            return None

        return single


def get_graph() -> ActivityPubGraph:
    graph = ActivityPubGraph("SQLAlchemy", identifier=str(VOC.Instance))
    # FIXME Make configurable
    graph.open("sqlite:///graph.db", create=True)

    # FIXME Remove
    from glob import glob
    for f in glob("/home/nik/Privat/Vocata/test/*.json"):
        graph.parse(f, format="json-ld")

    return graph
