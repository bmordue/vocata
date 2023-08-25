from starlette.testclient import TestClient
from starlette import status
from vocata.graph import ActivityPubGraph

# from vocata.graph.schema import AS
from vocata.server.signin import AUTH_ERROR


def test_signin_page(webclient: TestClient):
    resp = webclient.get("/auth/signin")
    assert resp.status_code == 200
    assert "Signin" in str(resp.content)


def test_signin_empty_post(webclient: TestClient):
    resp = webclient.post("/auth/signin", follow_redirects=False)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    redir_path = f"/auth/signin?error={AUTH_ERROR}"
    assert redir_path in str(resp.content)
    assert redir_path in str(resp.content)


def test_signin_success(webclient: TestClient, graph: ActivityPubGraph, get_actors):
    """Should be able to webfinger actors by their canonical URI"""
    with get_actors(1, webclient.base_url) as (actor_iri,):
        graph.set_actor_password(actor_iri, "pass")
        user = "pytest0@testserver"

        resp = webclient.post("/auth/signin", data={"user": user, "password": "pass"})
        assert resp.status_code == status.HTTP_200_OK
        redir_path = "/admin"
        assert redir_path in str(resp.content)


def test_signin_failure(webclient: TestClient, graph: ActivityPubGraph, get_actors):
    """Should be able to webfinger actors by their canonical URI"""
    with get_actors(1, webclient.base_url) as (actor_iri,):
        graph.set_actor_password(actor_iri, "pass")
        user = "pytest0@testserver"

        resp = webclient.post("/auth/signin", data={"user": user, "password": "noneshallpass"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        redir_path = f"/auth/signin?error={AUTH_ERROR}"
        assert redir_path in str(resp.content)


# FIXME: test is broken as the session or something doesn't survive the
# two test requests, though it works in the browser
def test_dashboard(webclient: TestClient, graph: ActivityPubGraph, get_actors):
    with get_actors(1, webclient.base_url) as (actor_iri,):
        graph.set_actor_password(actor_iri, "pass")
        user = "pytest0@testserver"

        # login
        resp = webclient.post("/auth/signin", data={"user": user, "password": "pass"})
        assert resp.status_code == status.HTTP_200_OK
        print(f"webclient cookies: {webclient.cookies}")

        # load dashboard
        resp = webclient.get("/admin")
        # WOMP WOMP why doesn't this work? (works in browser)
        # 401 unauth here because the ActivityPubActor middleware
        # is kicking in for some reason
        assert resp.status_code == status.HTTP_200_OK
