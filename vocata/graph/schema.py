from rdflib.namespace import Namespace, RDF

AS_URI = "https://www.w3.org/ns/activitystreams#"
AS = Namespace(AS_URI)

VOC_URI = "https://docs.vocata.one/information-schema#"
VOC = Namespace(VOC_URI)

LDP_URI = "http://www.w3.org/ns/ldp#"
LDP = Namespace(LDP_URI)

SEC_URI = "https://w3id.org/security#"
SEC = Namespace(SEC_URI)

__all__ = ["AS", "VOC", "LDP", "RDF", "SEC"]
