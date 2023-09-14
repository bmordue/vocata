import rdflib

from vocata.graph.schema import VOC, VCARD


def test_get_users(graph, client, get_actors, get_prefix):
    with (
        get_actors(2, client.base_url) as (actors),
        get_prefix(client.base_url) as (prefix, domain),
    ):
        with graph:
            for i, a in enumerate(actors):
                graph.set((a, VCARD.email, rdflib.Literal(f"mailto:pytest{i}@{domain}")))
                graph.set((a, VOC.hasServerRole, rdflib.Literal("role")))

            # nouser = graph.get_user(username="doesntexist")
            # assert nouser is None

            user = graph.get_user(username="pytest0")

            users = graph.get_users()

        assert user.actor == rdflib.URIRef(f"{client.base_url}/users/pytest0")
        assert str(user.name) == "Pytest Test Person 0"
        assert str(user.role) == "role"
        assert str(user.username) == "pytest0"
        assert str(user.localdomain) == domain
        assert str(user.email) == f"mailto:pytest0@{user.localdomain}"

        assert len(users) == 2
        for i, u in enumerate(users):
            assert u.actor == rdflib.URIRef(f"{client.base_url}/users/pytest{i}")
            assert str(u.name) == f"Pytest Test Person {i}"
            assert str(u.role) == "role"
            assert str(u.username) == f"pytest{i}"
            assert str(u.localdomain) == domain
            assert str(u.email) == f"mailto:pytest{i}@{u.localdomain}"


def test_update_user(graph, client, get_actors, get_prefix):
    with get_actors(1, client.base_url) as (actor,):
        with graph:
            actor = rdflib.URIRef(actor)
            user = graph.get_user(actor=actor)
            assert user

            graph.update_user(
                actor,
                email="mailto:foo",
                name="POWER USER",
                role="admin",
            )

            user = graph.get_user(actor=actor)
            assert str(user.email) == "mailto:foo"
            assert str(user.name) == "POWER USER"
            assert str(user.role) == "admin"


def test_get_prefix_row(graph, client, get_actors, get_prefix):
    no_actors_prefix = "https://noactorsprefix"
    one_actor_prefix = "https://oneactorprefix"
    one_actor_domain = "oneactorprefix"

    with (
        get_actors(2, client.base_url) as (default_actors),
        get_actors(1, one_actor_prefix) as (one_actors),
        get_prefix(no_actors_prefix) as (no_actors_prefix_uri, no_actors_domain),
        get_prefix(one_actor_prefix) as (one_actor_prefix_uri, one_actor_domain),
        get_prefix(client.base_url) as (prefix, domain),
    ):
        with graph:
            data = graph.get_prefixes()

            # 2 rows, since no_actors_prefix has no users
            assert len(data) == 2, f"wrong data len: {data}"
            row1, row2 = data

            print(row1)
            print(row2)

            assert str(row1.prefix) == prefix
            assert str(row1.domain) == domain
            assert int(row1.prefixUsers) == len(default_actors)
            assert row1.isLocal is not None

            assert str(row2.prefix) == one_actor_prefix
            assert str(row2.domain) == one_actor_domain
            assert int(row2.prefixUsers) == len(one_actors)
            assert row2.isLocal is not None
