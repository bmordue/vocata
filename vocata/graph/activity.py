import rdflib

from .schema import ACTIVITY_TYPES, AS, RDF


class ActivityPubActivityMixin:
    def handle_activities(self, doc: dict, target: str, request_actor: str):
        self._logger.debug("Handling activity to target %s for actor %s", target, request_actor)
        target = rdflib.URIRef(target)
        request_actor = rdflib.URIRef(target)

        # Add activity to a new subgraph for verification and transformation
        new_g = self.__class__()
        new_g.add_jsonld(doc, allow_non_local=True)

        # Discover all activities in new subgraph
        #   probably only one in ActivityPub, but there is no technical limit
        activities = set()
        for type_pred in ACTIVITY_TYPES:
            activities |= set(new_g.objects(subject=None, predicate=type_pred))

        # FIXME Synthesize Create activities for objects without activity

        results = set()
        for activity in activities:
            activity_type = new_g.value(subject=activity, predicate=RDF.type)
            if activity_type is None:
                raise KeyError("Activity %s has no type", activity)

            actors = set(new_g.objects(subject=activity, predicate=AS.actor))
            if len(actors) == 0:
                # If actor is not provided, assume authenticated actor of request
                self._logger.debug("Assuming actor of %s is %s", activity, request_actor)
                new_g.add((activity, AS.actor, request_actor))
            elif len(actors) > 1:
                # FIXME handle through proper schema validation
                raise TypeError("Activity %s has more than one actor", activity)
            elif actors[0] != request_actor:
                raise ValueError(
                    "Acttor of activity %s is different from request actor %s",
                    activity,
                    request_actor,
                )
            actor = actors[0]

            if self.is_an_outbox(target):
                # For new activities in outboxes (C2S) new IDs must be assigned
                activity = new_g.reassign_id(
                    activity, self.get_url_prefix(actor), fallback_ns="Activity"
                )

            objects = set(new_g.objects(subject=activity, predicate=AS.object))
            if len(objects) == 0:
                raise KeyError("Activity %s has no objects", activity)
            elif len(objects) > 1:
                raise TypeError("Activity %s has more than one object", activity)
            object_ = objects[0]

            activity_type_name = activity_type.fragment.lower()
            func = getattr(self, f"handle_{activity_type_name}_activity", None)
            if func is None:
                raise KeyError("No handler implemented for %s", activity_type_name)
            res = func(activity, object_, target)
            results.add(res)


__all__ = ["ActivityPubActivityMixin"]
