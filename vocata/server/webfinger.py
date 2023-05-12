# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

# FIXME move to useful code location, together with client.py
CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class WebfingerEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        resource = request.query_params.get("resource")
        if resource is None:
            return JSONResponse({"error": "Resource not provided"}, 400)

        uri = request.state.graph.get_canonical_uri(resource)
        if uri is None:
            return JSONResponse({"error": "Subject not found"}, 404)

        jrd = {
            # FIXME support canonicalization
            "subject": resource,
            "links": [
                {
                    "rel": "self",
                    "type": CONTENT_TYPE,
                    "href": uri,
                },
            ],
        }

        return JSONResponse(jrd, media_type="application/jrd+json")
