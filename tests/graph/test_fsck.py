# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from vocata.graph.schema import AS, RDF, VOC


def test_fsck_prefix_service_actor(graph):
    # Intentionally set a local prefix without creating an actor
    prefix = graph.get_url_prefix("https://example.com")
    graph.set_local_prefix(prefix, create_actor=False)
    assert (prefix, RDF.type, AS.Service) not in graph

    problems = graph._fsck_prefix_service_actor(fix=False)
    assert problems > 0

    problems = graph._fsck_prefix_service_actor(fix=True)
    assert problems == 0
    assert (prefix, RDF.type, AS.Service) in graph


def test_fsck_webfingerhref(graph, get_actors):
    with get_actors(1) as (actor_iri,):
        assert (actor_iri, AS.alsoKnownAs, None) in graph
        assert (actor_iri, VOC.webfingerHref, None) not in graph
        acct = graph.value(subject=actor_iri, predicate=AS.alsoKnownAs)
        graph.remove((actor_iri, AS.alsoKnownAs, None))
        graph.add((actor_iri, VOC.webfingerHref, acct))

        problems = graph._fsck_webfingerhref(fix=False)
        assert problems > 0
        assert (actor_iri, AS.alsoKnownAs, None) not in graph
        assert (actor_iri, VOC.webfingerHref, None) in graph

        problems = graph._fsck_webfingerhref(fix=True)
        assert problems == 0
        assert (actor_iri, VOC.webfingerHref, None) not in graph
        assert (acct, AS.alsoKnownAs, actor_iri) in graph
        assert (actor_iri, AS.alsoKnownAs, acct) in graph
