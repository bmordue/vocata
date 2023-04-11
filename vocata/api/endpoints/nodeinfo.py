from importlib.metadata import metadata
from typing import ClassVar

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...data import get_graph


class NodeInfoEndpoint(HTTPEndpoint):
    schema: ClassVar[str] = "http://nodeinfo.diaspora.software/ns/schema/2.1"

    async def get(self, request: Request) -> JSONResponse:
        meta = metadata("Vocata")
        graph = get_graph()

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
            "metadata": {
                "instance": {
                    "uuid": graph.instance_uuid,
                }
            },
        }

        return JSONResponse(nodeinfo, media_type=f'application/json; profile="{self.schema}#"')
