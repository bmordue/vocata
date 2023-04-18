from rdflib.namespace import Namespace, RDF

AS_URI = "https://www.w3.org/ns/activitystreams#"
AS = Namespace(AS_URI)

VOC_URI = "https://docs.vocata.one/information-schema#"
VOC = Namespace(VOC_URI)

LDP_URI = "http://www.w3.org/ns/ldp#"
LDP = Namespace(LDP_URI)

SEC_URI = "https://w3id.org/security#"
SEC = Namespace(SEC_URI)

# FIXME support intransitive activities
# FIXME disover from a real schema
ACTIVITY_TYPES = {
    AS.Create,
    AS.Update,
    AS.Delete,
    AS.Follow,
    AS.Add,
    AS.Remove,
    AS.Like,
    AS.Block,
    AS.Undo,
    AS.Accept,
    AS.Reject,
    AS.Announce,
}

__all__ = ["AS", "VOC", "LDP", "RDF", "SEC"]
