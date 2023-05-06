from httpx import BasicAuth
import pytest
from rdflib import Graph, URIRef, Literal, RDF
from starlette.testclient import TestClient
from vocata.graph.schema import AS, LDP
from vocata.util.http import HTTPSignatureAuth


AP_CONTENT_TYPES = {
    'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    "application/activity+json",
}

OBJECT_CONTEXT = "https://www.w3.org/ns/activitystreams"


def assert_object_jsonld_context(message: dict) -> None:
    message_context = message["@context"]
    assert (
        OBJECT_CONTEXT in message_context
        if isinstance(message_context, list)
        else OBJECT_CONTEXT == message_context
    )


ACTOR_CONTEXT = [OBJECT_CONTEXT, "https://w3id.org/security/v1"]


def assert_actor_jsonld_context(message: dict) -> None:
    message_context = message["@context"]
    for required_context in ACTOR_CONTEXT:
        assert required_context in message_context


def assert_collection(message: dict, *, iri: URIRef, ordered: bool, item_count: int):
    assert message[AS.id.fragment] == str(iri)
    type_ = AS.OrderedCollection if ordered else AS.Collection
    assert message[AS.type.fragment] == type_.fragment
    # Not required, but Vocata supplies it.
    assert AS.totalItems.fragment in message
    assert message[AS.totalItems.fragment] == item_count
    # No orderedItems when item_count is zero.
    items_ = AS.orderedItems if ordered else AS.items
    assert item_count == 0 or items_.Fragment in message
 

def set_up_actor(client: TestClient, graph: Graph) -> URIRef:
    acct_name = f"test@{client.base_url.netloc.decode()}"
    graph.create_actor_from_acct(acct_name, "Test Actor", "Person", False)
    return graph.value(predicate=RDF.type, object=AS.Person)


def set_up_note(client: TestClient, graph: Graph, content: str) -> URIRef:
    object_iri = URIRef(f"{client.base_url}/object/object-1")
    graph.set((object_iri, RDF.type, AS.Note))
    graph.set((object_iri, AS.content, Literal(content)))
    return object_iri


def test_get_actor_unauthenticated(client, app_graph):
    """Should be able to GET actors without authentication"""
    actor_iri = set_up_actor(client, app_graph)

    response = client.get(actor_iri)

    assert response.status_code == 200
    assert response.headers["Content-Type"] in AP_CONTENT_TYPES
    # TODO Create some utilities for common payload checks (@context, etc.)
    payload = response.json()
    assert_actor_jsonld_context(payload)
    assert payload[AS.id.fragment] == str(actor_iri)
    assert payload[AS.type.fragment] == AS.Person.fragment
    assert AS.inbox.fragment in payload


@pytest.mark.skip("FIXME - as:totalItems is not compacted.")
@pytest.mark.parametrize("box_pred", [LDP.inbox, AS.outbox])
def test_get_actor_box_unauthenticated(client: TestClient, app_graph: Graph, box_pred: URIRef) -> None:
    """Should be able to GET actor inbox and outbox without authentication"""
    actor_iri = set_up_actor(client, app_graph)
    box_iri = app_graph.value(subject=actor_iri, predicate=box_pred)

    response = client.get(box_iri)

    assert response.status_code == 200
    assert response.headers["Content-Type"] in AP_CONTENT_TYPES
    payload = response.json()
    assert_object_jsonld_context(payload)
    assert_collection(payload, iri=box_iri, ordered=True, item_count=0)


def test_get_public_object_unauthenticated(client, app_graph):
    """Should be able to GET public object without authentication"""
    object_iri = set_up_note(client, app_graph, "TEST_CONTENT")
    app_graph.set((object_iri, AS.audience, AS.Public))

    response = client.get(object_iri)

    assert response.status_code == 200
    assert response.headers["Content-Type"] in AP_CONTENT_TYPES
    payload = response.json()
    assert_object_jsonld_context(payload)
    assert payload[AS.id.fragment] == str(object_iri)
    assert payload[AS.type.fragment] == AS.Note.fragment
    assert payload[AS.content.fragment] == "TEST_CONTENT"


# TODO get addressed object with HTTP signature (S2S)?

def test_get_addressed_object_basic_auth(client, app_graph):
    """Authenticated client should be able to GET an object addressed to them."""
    actor_iri = set_up_actor(client, app_graph)
    password = "PASSWORD"
    app_graph.set_actor_password(str(actor_iri), password)
    account = app_graph.value(subject=actor_iri, predicate=AS.alsoKnownAs)
    # BasicAuth will be confused by the ":" since that's a delimiter for user:pass
    account = str(account).replace("acct:", "")
    object_iri = set_up_note(client, app_graph, "TEST_CONTENT")
    app_graph.set((object_iri, AS.audience, actor_iri))

    response = client.get(object_iri, auth=BasicAuth(account, password))

    assert response.status_code == 200
    assert response.headers["Content-Type"] in AP_CONTENT_TYPES
    payload = response.json()
    assert_object_jsonld_context(payload)
    assert payload[AS.id.fragment] == str(object_iri)
    assert payload[AS.type.fragment] == AS.Note.fragment
    assert "content" in payload


def test_get_private_object_unauthenticated(client, app_graph):
    """Unauthenticated requests for non-public objects should fail."""
    object_iri = set_up_note(client, app_graph, "TEST_CONTENT")

    response = client.get(object_iri)

    assert response.status_code == 401
