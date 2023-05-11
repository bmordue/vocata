# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from requests import Request

from vocata.util.http import HTTPSignatureAuth


def test_sign_verify(graph, get_actors):
    headers = ["(request-target)", "host", "date", "digest"]
    data = {"summary": "Test Data"}

    with get_actors() as actors:
        for actor in actors:
            auth = HTTPSignatureAuth(graph, headers, actor=actor)
            request = Request("POST", f"{actor}/test", json=data, auth=auth)

            prepared = request.prepare()
            assert "Signature" in prepared.headers

            # FIXME mock this correctly
            prepared.state = type("_State", tuple(), {"graph": graph})
            HTTPSignatureAuth.from_signed_request(prepared, pull=False).verify_request(prepared)
