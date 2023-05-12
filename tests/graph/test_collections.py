# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pytest
import rdflib

from vocata.graph.schema import AS


def _assert_collection_order(graph, collection, expected):
    items_node = graph.value(subject=collection, predicate=AS.items)
    reference_list = list(rdflib.collection.Collection(graph, items_node))
    assert reference_list == expected


def _assert_collection_order_jsonld(graph, actor_iri, collection, expected):
    reference_list = graph.activitystreams_cbd(str(collection), actor_iri).to_activitystreams(
        str(collection)
    )["orderedItems"]
    assert reference_list == list(map(str, expected))


def test_cannot_create_existing(graph, get_notes):
    with get_notes(1) as (note_iri,):
        with pytest.raises(TypeError):
            graph.create_collection(note_iri)


@pytest.mark.parametrize("insert_order", ([0, 1, 2, 3, 4], [4, 3, 2, 1, 0], [3, 1, 4, 0, 2]))
def test_ordered_add_remove(graph, get_actors, get_notes, insert_order):
    with get_actors(1) as (actor_iri,), get_notes(len(insert_order)) as notes:
        outbox = graph.get_actor_outbox(actor_iri)
        expected_order = []

        # Order after a row of inserts
        for note_id in insert_order:
            graph.add_to_collection(outbox, notes[note_id])
            expected_order.insert(0, notes[note_id])
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)

        # Order after deleting from middle
        graph.remove_from_collection(outbox, expected_order[1])
        removed_1 = expected_order.pop(1)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)
        graph.remove_from_collection(outbox, expected_order[2])
        removed_2 = expected_order.pop(2)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)

        # Order after re-adding
        graph.add_to_collection(outbox, removed_2)
        expected_order.insert(0, removed_2)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)
        graph.add_to_collection(outbox, removed_1)
        expected_order.insert(0, removed_1)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)

        # Order after deleting from start
        graph.remove_from_collection(outbox, expected_order[0])
        removed_1 = expected_order.pop(0)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)

        # Order after deleting from end
        graph.remove_from_collection(outbox, expected_order[-1])
        removed_2 = expected_order.pop(-1)
        _assert_collection_order(graph, outbox, expected_order)
        _assert_collection_order_jsonld(graph, actor_iri, outbox, expected_order)
