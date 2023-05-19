# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from rdflib import Literal

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


def test_fsck_alsoknownas_symmetric(graph, get_actors):
    with get_actors(1) as (actor_iri,):
        acct = graph.value(subject=actor_iri, predicate=AS.alsoKnownAs)
        assert (acct, AS.alsoKnownAs, actor_iri) in graph

        graph.remove((acct, AS.alsoKnownAs, actor_iri))
        assert (acct, AS.alsoKnownAs, actor_iri) not in graph

        problems = graph._fsck_alsoknownas_symmetric(fix=False)
        assert problems > 0
        assert (acct, AS.alsoKnownAs, actor_iri) not in graph

        problems = graph._fsck_alsoknownas_symmetric(fix=True)
        assert problems == 0
        assert (acct, AS.alsoKnownAs, actor_iri) in graph


def test_fsck_ordereditems_predicate(graph, get_actors, get_notes):
    with get_actors(1) as (actor_iri,), get_notes() as notes:
        outbox = graph.value(subject=actor_iri, predicate=AS.outbox)
        for note_iri in notes:
            graph.add((outbox, AS.orderedItems, note_iri))

        problems = graph._fsck_ordereditems_predicate(fix=False)
        assert problems == 1

        problems = graph._fsck_ordereditems_predicate(fix=True)
        assert problems == 0
        assert (outbox, AS.items / RDF.first, None) in graph


def test_fsck_totalitems_orderedcollection(graph, get_actors, get_notes):
    with get_actors(1) as (actor_iri,), get_notes() as notes:
        outbox = graph.value(subject=actor_iri, predicate=AS.outbox)
        for note_iri in notes:
            graph.add_to_collection(outbox, note_iri)
        assert graph.value(subject=outbox, predicate=AS.totalItems).value == 3

        graph.set((outbox, AS.totalItems, Literal(5)))

        problems = graph._fsck_totalitems(fix=False)
        assert problems == 1

        problems = graph._fsck_totalitems(fix=True)
        assert problems == 0
        assert graph.value(subject=outbox, predicate=AS.totalItems).value == 3


def test_fsck_totalitems_collection(graph, get_actors, get_notes):
    with get_actors(1) as (actor_iri,), get_notes() as notes:
        followers = graph.value(subject=actor_iri, predicate=AS.followers)
        for note_iri in notes:
            graph.add_to_collection(followers, note_iri)
        assert graph.value(subject=followers, predicate=AS.totalItems).value == 3

        graph.set((followers, AS.totalItems, Literal(5)))

        problems = graph._fsck_totalitems(fix=False)
        assert problems == 1

        problems = graph._fsck_totalitems(fix=True)
        assert problems == 0
        assert graph.value(subject=followers, predicate=AS.totalItems).value == 3
