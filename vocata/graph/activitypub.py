from uuid import uuid4

import rdflib

from .actor import ActivityPubActorMixin
from .authz import ActivityPubAuthzMixin
from .federation import ActivityPubFederationMixin
from .jsonld import JSONLDMixin
from .schema import RDF, VOC


class ActivityPubGraph(
    rdflib.Graph,
    ActivityPubAuthzMixin,
    ActivityPubActorMixin,
    JSONLDMixin,
    ActivityPubFederationMixin,
):
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


__all__ = ["ActivityPubGraph"]
