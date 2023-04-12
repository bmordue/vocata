import json
from enum import Enum
from uuid import uuid4

import rdflib
from pyld import jsonld
from rdflib.namespace import NamespaceManager, RDF
from rdflib.parser import PythonInputSource

from .util import jsonld_single, jsonld_cleanup_ids

AS_URI = "https://www.w3.org/ns/activitystreams#"
AS = rdflib.Namespace(AS_URI)

VOC_URI = "https://docs.vocata.one/information-schema#"
VOC = rdflib.Namespace(VOC_URI)

LDP_URI = "http://www.w3.org/ns/ldp#"
LDP = rdflib.Namespace(LDP_URI)

SEC_URI = "https://w3id.org/security#"
SEC = rdflib.Namespace(SEC_URI)

# FIXME validate against spec
HAS_AUDIENCE = AS.audience | AS.to | AS.bto | AS.cc | AS.bcc
HAS_ACTOR = AS.actor | AS.attributedTo

HAS_BOX = LDP.inbox | AS.outbox

PUBLIC_ACTOR = AS.Public

HIDE_PREDICATES = {AS.bto, AS.bcc, SEC.privateKey, SEC.privateKeyPem}


class AccessMode(Enum):
    READ = 1
    WRITE = 2


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

    def get_actor_uri_by_acct(self, acct: str) -> str | None:
        uri = self.value(subject=acct, predicate=VOC.webfingerHref)
        if uri is None:
            return None
        return str(uri)

    def is_a_box(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, HAS_BOX, subject) in self

    def is_an_actor(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, AS.actor, subject) in self

    def is_sender(self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str) -> bool:
        return (subject, HAS_ACTOR, actor) in self

    def is_recipient(self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str) -> bool:
        return (subject, HAS_AUDIENCE, actor) in self

    def is_public(self, subject: rdflib.term.Identifier | str) -> bool:
        return (subject, HAS_AUDIENCE, PUBLIC_ACTOR) in self

    def is_box_owner(self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str) -> bool:
        return (actor, HAS_BOX, subject) in self and self.is_a_box(subject)

    def is_authorized(self, actor: rdflib.URIRef | str, subject: rdflib.term.Identifier | str, mode: AccessMode = AccessMode.READ) -> bool:
        if mode == AccessMode.READ:
            if self.is_public(subject):
                # Activities posted to the special Public audience can be read
                return True
            if self.is_an_actor(subject):
                # Actor objects can generally be read
                return True
            if self.is_sender(actor, subject):
                # Senders may read their own activities
                return True
            if self.is_recipient(actor, subject):
                # Direct recipients may see activities
                return True
        elif mode == AccessMode.WRITE:
            if self.is_box_owner(actor, subject):
                # Owners of inboxes and outboxes can write to their boxes
                return True

        return False

    def filter_authorized(
        self, actor: rdflib.URIRef | str, root_graph: rdflib.Graph | None = None
    ) -> rdflib.Graph:
        if root_graph is None:
            root_graph = self

        new_g = self.__class__()

        for subject in self.subjects():
            if root_graph.is_authorized(actor, subject):
                for s, p, o in self.triples((subject, None, None)):
                    if s in VOC or p in VOC or o in VOC:
                        # Never expose any triples involving local information scheme
                        continue
                    if p in HIDE_PREDICATES:
                        # Never expose some triples, see above
                        continue
                    new_g.add((s, p, o))

        return new_g

    def to_activitystreams(self) -> dict:
        profile = AS_URI.removesuffix("#")

        doc = json.loads(self.serialize(format="json-ld"))

        framed = jsonld.frame(doc, profile, options={"embed": "@always"})
        compacted = jsonld.compact(framed, profile)

        return compacted

    def get_single_activitystream(self, uri: str, actor: str = str(PUBLIC_ACTOR)) -> dict | None:
        doc = (
            self.cbd(rdflib.URIRef(uri), target_graph=self.__class__())
            .filter_authorized(actor, self)
            .to_activitystreams()
        )
        try:
            single = jsonld_cleanup_ids(jsonld_single(doc, uri))
        except KeyError:
            return None

        return single

    def get_public_key_by_id(self, id_: rdflib.term.Identifier | str) -> str:
        pem = self.value(subject=id_, predicate=SEC.publicKeyPem)
        if pem is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        return str(pem)

    def get_public_key(self, actor: rdflib.term.Identifier | str) -> tuple[str, str]:
        id_ = self.value(subject=actor, predicate=SEC.publicKey)
        if id_ is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        pem = self.get_public_key_by_id(id_)
        return str(id_), str(pem)

    def get_private_key_by_id(self, id_: rdflib.term.Identifier | str) -> str:
        pem = self.value(subject=id_, predicate=SEC.privateKeyPem)
        if pem is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        return str(pem)

    def get_private_key(self, actor: rdflib.term.Identifier | str) -> tuple[str, str]:
        id_ = self.value(subject=actor, predicate=SEC.privateKey)
        if id_ is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        pem = self.get_private_key_by_id(id_)

        return str(id_), str(pem)

    def add_activitystream(self, data: dict) -> rdflib.Graph:
        # Parse into a new graph first, in case something fails
        new_g = rdflib.Graph()
        source = PythonInputSource(data, data["id"])
        new_g.parse(source, format="json-ld")

        # Remvoe all statements about subject and add new
        self.remove((data["id"], None, None))
        self += new_g

        return new_g

def get_graph() -> ActivityPubGraph:
    graph = ActivityPubGraph("SQLAlchemy", identifier=str(VOC.Instance))
    # FIXME Make configurable
    graph.open("sqlite:///graph.db", create=True)

    # FIXME Remove
    from glob import glob
    for f in glob("/home/nik/Privat/Vocata/test/*.json"):
        graph.parse(f, format="json-ld")
    graph.add((rdflib.URIRef("acct:tester@vocatadev.pagekite.me"), VOC.webfingerHref, rdflib.URIRef("https://vocatadev.pagekite.me/users/tester")))

    return graph
