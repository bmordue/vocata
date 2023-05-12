# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from starlette.testclient import TestClient

from vocata.graph.schema import AS

# FIXME move to useful code location, together with client.py
AP_CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


def test_webfigner_https(client: TestClient, get_actors):
    """Should be able to webfigner actors by their canonical URI"""
    with get_actors(1, client.base_url) as (actor_iri,):
        resource = str(actor_iri)
        expected_href = str(actor_iri)
        response = client.get(f"{client.base_url}/.well-known/webfinger?resource={resource}")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/jrd+json"

        payload = response.json()
        assert payload["subject"] == resource
        assert {
            "rel": "self",
            "type": AP_CONTENT_TYPE,
            "href": expected_href,
        } in payload["links"]


def test_webfigner_acct(client: TestClient, graph, get_actors):
    """Should be able to webfigner actors by their user@domain account"""
    with get_actors(1, client.base_url) as (actor_iri,):
        user = graph.value(subject=actor_iri, predicate=AS.preferredUsername)
        domain = client.base_url.netloc.decode()
        resource = f"acct:{user}@{domain}"

        expected_href = str(actor_iri)

        response = client.get(f"{client.base_url}/.well-known/webfinger?resource={resource}")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/jrd+json"

        payload = response.json()
        assert payload["subject"] == resource
        assert {
            "rel": "self",
            "type": AP_CONTENT_TYPE,
            "href": expected_href,
        } in payload["links"]


def test_webfigner_no_resource(client: TestClient):
    """Webfinger without resource should return error"""
    response = client.get(f"{client.base_url}/.well-known/webfinger")
    assert response.status_code == 400


def test_webfigner_nonexisting(client: TestClient):
    """Webfinger with non-existing resource should return error"""
    response = client.get(
        f"{client.base_url}/.well-known/webfinger?resource=acct:nonexistent@bad.example.com"
    )
    assert response.status_code == 404
