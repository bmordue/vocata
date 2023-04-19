from typing import TYPE_CHECKING

import rdflib

from .schema import ACTIVITY_TYPES, AS, OBJECT_TYPES, RDF

if TYPE_CHECKING:
    from .activitypub import ActivityPubGraph


class ActivityPubActivityMixin:
    def handle_jsonld_activity(self, doc: dict, target: str, request_actor: str) -> rdflib.URIRef:
        self._logger.debug("Handling activity to target %s for actor %s", target, request_actor)
        target = rdflib.URIRef(target)
        request_actor = rdflib.URIRef(target)

        # Add activity to a new subgraph for verification and transformation
        new_g = self.__class__()
        new_g.add_jsonld(doc, allow_non_local=True)
        return self.handle_activity_subgraph(self, new_g, target, request_actor)

    def handle_activity_subgraph(
        self, new_g: "ActivityPubGraph", target: str, request_actor: str
    ) -> rdflib.URIRef:
        # Activities received over ActivityPub must contain
        #  exactly one activity or one object (to create it).
        #  In graph terms, this is true if the incoming
        #  subgraph is "rooted" (it has a node which appears
        #  only as subject and never as object) and connected
        #  (all nodes can be reached from there)
        roots = set(new_g.roots())
        if len(roots) != 1:
            raise TypeError("The activity graph must have exactly one root")
        if not new_g.connected():
            raise TypeError("The activity graph must be connected")
        root = roots.pop()

        # Work on the CBD (Concise Bounded Description) of the root
        #  node from here. This ensures we are not receiving spoofed
        #  publicly dereferencable objects; we will pull any referenced
        #  objects again later
        new_cbd = new_g.cbd(root)

        root_type = new_cbd.value(subject=root, predicate=RDF.type)
        if root_type in OBJECT_TYPES:
            # If the root is an object, assume a Create activity
            # FIXME implement
            activity = ...
        elif root_type in ACTIVITY_TYPES:
            activity = root
        else:
            raise TypeError("The root object is neither an Activity nor an Object")

        # FIXME continue implementation
        raise NotImplementedError()


__all__ = ["ActivityPubActivityMixin"]
