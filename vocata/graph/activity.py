from datetime import datetime
from typing import TYPE_CHECKING

import rdflib

from .authz import AccessMode, HAS_BOX, PUBLIC_ACTOR
from .schema import ACTIVITY_TOUCHES, ACTIVITY_TYPES, AS, OBJECT_TYPES, RDF, VOC

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
        # FIXME Do we need to verify the ID for inbox posts?
        #  i.e. to not overwrite an existing activity, or to prevent spoofing?

        # Only activities by the requesting actor must be handled
        actor = new_cbd.value(subject=activity, predicate=AS.actor)
        if actor is None:
            self._logger.warning("Incoming activity has no actor; assuming from request")
            new_cbd.set((activity, AS.actor, rdflib.URIRef(request_actor)))
        elif str(actor) != str(request_actor):
            raise ValueError(
                "Activity actor %s is not the authenticated actor %s", actor, request_actor
            )
        # FIXME also check that box owner is in audience?

        # Amend activity with some functional values for later processing
        new_cbd.set((activity, VOC.receivedAt, rdflib.Literal(datetime.now())))
        new_cbd.set((activity, VOC.processed, rdflib.Literal(False)))

        # Merge into main graph
        #  As we ensured to handle a CBD above, we can be certain not to
        #  override or add subjects here. All additions to the graph
        #  except for the activity will be carried out as side effect,
        #  with a clean pull from the authoritative origin.
        # Side effects will be carried out separately
        self += new_cbd
        self.add_to_collection(target, activity)
        self._logger.info("Activity %s added to graph", activity)

        return activity

    async def carry_out_activity(
        self, activity: rdflib.URIRef, box: rdflib.URIRef = PUBLIC_ACTOR, force: bool = False
    ):
        self._logger.debug("Determining recipient of %s from box %s", activity, box)
        # FIXME is this correct?
        recipient = self.value(predicate=HAS_BOX, object=box, any=True)
        self._logger.info("Carrying out activity %s for %s", activity, recipient)

        type_ = self.value(subject=activity, predicate=RDF.type)
        if type_ not in ACTIVITY_TYPES:
            raise TypeError(f"{activity} is not an activity type")

        processed = self.value(subject=activity, predicate=VOC.processed, default=False)
        if processed and not force:
            self._logger.warning("Activity %s already processed", activity)

        # FIXME we might want to process other activities that touch the
        #  same object/target/… and have been received earlier here?

        # Pull all objects related to the activity
        touches = self.objects(activity, ACTIVITY_TOUCHES, unique=True)
        for touch in touches:
            self._logger.debug("Activity touches %s, pulling", touch)
            self.pull(touch, recipient)

        actor = self.value(subject=activity, predicate=AS.actor, default=PUBLIC_ACTOR)

        object_ = self.value(subject=activity, predicate=AS.object)
        if object_ is None:
            raise KeyError(f"Activity {activity} does not have an object")

        func_name = f"carry_out_{type_.fragment.lower()}"
        func = getattr(self, func_name, None)
        if func is None:
            raise NotImplementedError()

        try:
            results = func(activity, actor, object_, recipient)
        # FIXME use proper exception handling
        except Exception as ex:
            self.set((activity, VOC.processRessult, rdflib.Literal(str(ex))))
            raise

        for result in results:
            self.add((activity, VOC.processResult, rdflib.Literal(result)))
        self.set((activity, VOC.processed, rdflib.Literal(True)))
        self.set((activity, VOC.processedAt, rdflib.Literal(datetime.now())))

    def carry_out_accept(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        object_type = self.value(subject=object_, predicate=RDF.type)
        if object_type is None:
            raise TypeError(f"{object_} has no type")

        # We might have a handler for accepting this type of object
        func_name = f"carry_out_accept_{object_type.fragment.lower()}"
        func = getattr(self, func_name, None)
        if func is None:
            return {"no side effects to carry out"}
        return func(activity, actor, object_, recipient)

    def carry_out_accept_follow(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        follow_activity: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        followed_object = self.value(subject=follow_activity, predicate=AS.object)
        if followed_object is None:
            raise ValueError(f"Original follow activity {follow_activity} has no object")

        if not self.is_authorized(actor, followed_object, AccessMode.ACCEPT_FOLLOW):
            # FIXME use proper exception
            raise Exception(f"Actoor {actor} is not authorized to accept {follow_activity}")

        collection = self.value(subject=recipient, predicate=AS.following)
        if collection is None:
            # FIXME create collection
            self._logger.warning("Actor %s does not have a following collection", recipient)
            return {f"{recipient} does not have following collection; no side effects to carry out"}

        self.add_to_collection(collection, actor)
        return {f"actor added to following collection of {recipient}"}

    def carry_out_reject(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        object_type = self.value(subject=object_, predicate=RDF.type)
        if object_type is None:
            raise TypeError(f"{object_} has no type")

        # We might have a handler for accepting this type of object
        func_name = f"carry_out_reject_{object_type.fragment.lower()}"
        func = getattr(self, func_name, None)
        if func is None:
            return {"no side effects to carry out"}
        return func(activity, actor, object_, recipient)

    def carry_out_reject_follow(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        follow_activity: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        followed_object = self.value(subject=follow_activity, predicate=AS.object)
        if followed_object is None:
            raise ValueError(f"Original follow activity {follow_activity} has no object")

        if not self.is_authorized(actor, followed_object, AccessMode.REJECT_FOLLOW):
            # FIXME use proper exception
            raise Exception(f"Actoor {actor} is not authorized to reject {follow_activity}")

        collection = self.value(subject=recipient, predicate=AS.following)
        if collection is None:
            # FIXME create collection
            self._logger.warning("Actor %s does not have a following collection", recipient)
            return {f"{recipient} does not have following collection; no side effects to carry out"}

        self.remove_from_collection(collection, actor)
        return {f"actor removed from following collection of {recipient}"}

    def carry_out_create(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        # The activity has been added to the inbox already
        #  and the object has been pulled already
        return {"no side effects to carry out"}

    def carry_out_delete(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        if not self.is_authorized(actor, object_, AccessMode.DELETE):
            # FIXME use proper exception
            raise Exception(f"Actoor {actor} is not authorized to delete {object_}")

        self._logger.info("Removing %s from graph", object_)
        self.remove((object_, None, None))

        self._logger.debug("Synthesizing tombstone at %s", object_)
        # FIXME should we set a deleted date?
        self.set((rdflib.URIRef(object_), RDF.type, AS.Tombstone))

        return {f"replaced {object_} with tombstone"}

    def carry_out_follow(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        # The activity has been added to the inbox already
        #  and we don't want to auto-accept for now
        return {"no side effects to carry out"}

    def carry_out_update(
        self,
        activity: rdflib.URIRef,
        actor: rdflib.URIRef,
        object_: rdflib.URIRef,
        recipient: rdflib.URIRef = PUBLIC_ACTOR,
    ) -> set[str]:
        # The object has been pulled already
        return {"no side effects to carry out"}


__all__ = ["ActivityPubActivityMixin"]
