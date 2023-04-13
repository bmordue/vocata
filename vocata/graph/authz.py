from enum import StrEnum

import rdflib
from rdflib.paths import ZeroOrMore

from .schema import AS, LDP, SEC, VOC

# FIXME validate against spec
HAS_AUDIENCE = AS.audience | AS.to | AS.bto | AS.cc | AS.bcc
HAS_TRANSIENT_AUDIENCE = HAS_AUDIENCE / (AS.items * ZeroOrMore)
# FIXME support shared inboxes
HAS_TRANSIENT_INBOXES = HAS_TRANSIENT_AUDIENCE / LDP.inbox
HAS_ACTOR = AS.actor
HAS_AUTHOR = AS.actor | AS.attributedTo
HAS_BOX = LDP.inbox | AS.outbox | AS.followers | AS.following

PUBLIC_ACTOR = AS.Public

HIDE_PREDICATES = {AS.bto, AS.bcc, SEC.privateKey, SEC.privateKeyPem}


class AccessMode(StrEnum):
    READ = "read"
    WRITE = "write"


class ActivityPubAuthzMixin:
    def is_a_box(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, HAS_BOX, subject) in self

    def is_an_actor(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, AS.actor, subject) in self

    def is_an_actor_public_key(self, subject: rdflib.term.Identifier | str) -> bool:
        return (None, AS.actor / SEC.publicKey, subject) in self

    def is_author(
        self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str
    ) -> bool:
        return (subject, HAS_AUTHOR, actor) in self

    def is_recipient(
        self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str
    ) -> bool:
        return (subject, HAS_AUDIENCE, actor) in self

    def is_public(self, subject: rdflib.term.Identifier | str) -> bool:
        return (subject, HAS_AUDIENCE, PUBLIC_ACTOR) in self

    def is_box_owner(
        self, actor: rdflib.term.Identifier | str, subject: rdflib.term.Identifier | str
    ) -> bool:
        return (actor, HAS_BOX, subject) in self and self.is_a_box(subject)

    def is_authorized(
        self,
        actor: rdflib.URIRef | str,
        subject: rdflib.term.Identifier | str,
        mode: AccessMode = AccessMode.READ,
    ) -> bool:
        action, reason = False, "no authz rule matched"
        if mode == AccessMode.READ:
            if self.is_public(subject):
                # Activities posted to the special Public audience can be read
                action, reason = True, "is targeted at public"
            elif self.is_an_actor(subject):
                # Actor objects can generally be read
                action, reason = True, "is an actor"
            elif self.is_a_box(subject):
                # Inboxes, outboxes, and follower, following are readable
                action, reason = True, "is a box collection"
            elif self.is_an_actor_public_key(subject):
                # Public keys of actors can be read
                action, reason = True, "is an actor public key"
            elif self.is_author(actor, subject):
                # Senders may read their own activities
                action, reason = True, "is author of object"
            elif self.is_recipient(actor, subject):
                # Direct recipients may see activities
                action, reason = True, "is recipient of object"
        elif mode == AccessMode.WRITE:
            if self.is_box_owner(actor, subject):
                # Owners of inboxes and outboxes can write to their boxes
                action, reason = True, "is owner of box collection"

        action_name = "Grant" if action else "Deny"
        self._logger.debug(
            "%sing %s access on %s to %s: %s", action_name, mode.value, subject, actor, reason
        )
        return action

    def filter_authorized(
        self, actor: rdflib.URIRef | str, root_graph: rdflib.Graph | None = None
    ) -> rdflib.Graph:
        if root_graph is None:
            root_graph = self

        self._logger.debug("Filtering (sub)graph using authorization rules")

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


__all__ = ["AccessMode", "ActivityPubAuthzMixin"]
