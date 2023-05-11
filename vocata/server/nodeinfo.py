# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from importlib.metadata import metadata
from typing import ClassVar

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse


class NodeInfoEndpoint(HTTPEndpoint):
    schema: ClassVar[str] = "http://nodeinfo.diaspora.software/ns/schema/2.1"

    async def get(self, request: Request) -> JSONResponse:
        meta = metadata("Vocata")

        nodeinfo = {
            "version": "2.1",
            "software": {
                "name": meta["Name"],
                "version": meta["Version"],
                # "repository": "",  # FIXME implement
                # "homepage": "",  # FIXME implement
            },
            "protocols": ["activitypub"],
            "services": {"inbound": [], "outbound": []},
            "openRegistrations": False,  # FIXME implement
            "usage": {
                "users": {
                    "total": 0,  # FIXME implement
                    "activeHalfyear": 0,  # FIXME implement
                    "activeMonth": 0,  # FIXME implement
                },
                "localPosts": 0,  # FIXME implement
                "localComments": 0,  # FIXME implement
            },
            "metadata": {},
        }

        return JSONResponse(nodeinfo, media_type=f'application/json; profile="{self.schema}#"')


def nodeinfo_wellknown(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "links": [
                {
                    "rel": NodeInfoEndpoint.schema,
                    "href": str(request.url_for("functional:nodeinfo")),
                }
            ]
        }
    )
