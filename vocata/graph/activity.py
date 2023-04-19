from datetime import datetime
from typing import TYPE_CHECKING

import rdflib

from .schema import ACTIVITY_TYPES, AS, OBJECT_TYPES, RDF, VOC

if TYPE_CHECKING:
    from .activitypub import ActivityPubGraph


class ActivityPubActivityMixin:
    def handle_activity_jsonld(self, doc: dict, target: str, request_actor: str) -> rdflib.URIRef:
        self._logger.debug("Handling activity to target %s for actor %s", target, request_actor)
        target = rdflib.URIRef(target)
        request_actor = rdflib.URIRef(request_actor)

        # Add activity to a new subgraph for verification and transformation
        new_g = self.__class__()
        new_g.add_jsonld(doc, allow_non_local=True)
        return self.handle_activity_subgraph(new_g, target, request_actor)

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
        self._logger.debug("Incoming object is of type %s", root_type)
        if root_type in ACTIVITY_TYPES:
            self._logger.debug("%s is an actitiy type", root)
            activity = root
        elif root_type in OBJECT_TYPES:
            if self.is_an_outbox(target):
                # If the root is an object, assume a Create activity
                # FIXME implement
                raise NotImplementedError("Implicit Create not implemented")
            else:
                raise TypeError("The root ist not an Activity")
        else:
            raise TypeError("The root is neither an Activity nor an Object")

        # Every activity must have exactly one object
        object_ = new_cbd.value(subject=activity, predicate=AS.object)
        if object_ is None:
            raise KeyError("No object defined")

        if self.is_an_outbox(target):
            # Outbox activities and objects must get reassigned IDs
            self._logger.debug("Received activity at outbox; reassining IDs")
            new_cbd.reassign_id(activity, target, "Activity")
            new_cbd.reassign_id(object_, target)

        # Only activities by the requesting actor must be handled
        actor = new_cbd.value(subject=activity, predicate=AS.actor)
        if actor is None:
            self._logger.warning("Incoming activity has no actor; assuming from request")
            new_cbd.set((activity, AS.actor, rdflib.URIRef(request_actor)))
        elif str(actor) != str(request_actor):
            raise ValueError(
                "Activity actor %s is not the authenticated actor %s", actor, request_actor
            )

        # Amend activity with some functional values for later processing
        new_cbd.set((activity, VOC.receivedAt, rdflib.Literal(datetime.now())))
        new_cbd.set((activity, VOC.processed, rdflib.Literal(False)))

        # Merge into main graph
        #  Side effects will be carried out separately
        self += new_cbd
        self.add_to_collection(target, activity)
        self._logger.info("Activity %s added to graph", activity)

        return activity

    async def carry_out_activity(self, activity: str):
        self._logger.info("Carrying out activity %s", activity)

        raise NotImplementedError()


__all__ = ["ActivityPubActivityMixin"]
