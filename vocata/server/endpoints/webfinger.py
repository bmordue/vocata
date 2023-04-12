from importlib.metadata import metadata
from typing import ClassVar

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

# FIXME move to useful code location, together with client.py
CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class WebfingerEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        acct = request.query_params.get("resource")
        if acct is None:
            return JSONResponse({"error": "Resource not provided"}, 400)
        if not acct.startswith("acct:"):
            return JSONResponse({"error": "Resource is invalid"}, 400)

        uri = request.state.graph.get_actor_uri_by_acct(acct)
        if uri is None:
            return JSONResponse({"error": "Subject not found"}, 404)

        jrd = {
            # FIXME support canonicalization
            "subject": acct,
            "links": [
                {
                    "rel": "self",
                    "type": CONTENT_TYPE,
                    "href": uri,
                },
            ],
        }

        return JSONResponse(jrd, media_type="application/jrd+json")
