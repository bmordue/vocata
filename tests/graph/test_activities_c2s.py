# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
# SPDX-FileCopyrightText: © 2023 Steve Bate <svc-codeberg@stevebate.net>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pytest
import rdflib

from vocata.graph.schema import AS


@pytest.fixture
def test_note():
    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Note",
        "content": "This is a note",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
    }


@pytest.fixture
def create_activities(test_note, get_actors):
    with get_actors() as actors:
        activities = []
        for actor in actors:
            activities.append(
                {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "type": "Create",
                    "actor": str(actor),
                    "object": test_note,
                }
            )
        yield activities


@pytest.mark.asyncio
async def test_create_activity(graph, get_prefix, create_activities):
    assigned_ids = set()

    with get_prefix() as (prefix, domain):
        for activity in create_activities:
            actor = activity["actor"]
            outbox = graph.get_actor_outbox(rdflib.URIRef(actor))

            activity_uri = graph.handle_activity_jsonld(activity, outbox, actor)

            assert activity_uri is not None
            assert activity_uri.startswith(prefix)
            assert activity_uri not in assigned_ids
            assigned_ids.add(activity_uri)

            object_uri = graph.value(subject=activity_uri, predicate=AS.object)
            assert isinstance(object_uri, rdflib.BNode)

            await graph.carry_out_activity(activity_uri, outbox)
            object_uri = graph.value(subject=activity_uri, predicate=AS.object)
            assert object_uri.startswith(prefix)
            assert object_uri not in assigned_ids
