from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .nodeinfo import NodeInfoEndpoint
from .webfinger import WebfingerEndpoint


def nodeinfo(request: Request) -> JSONResponse:
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


FUNCTIONAL = [
    Route("/nodeinfo", NodeInfoEndpoint, name="nodeinfo"),
]

WELL_KNOWN = [
    Route("/nodeinfo", nodeinfo, name="nodeinfo"),
    Route("/webfinger", WebfingerEndpoint, name="webfinger"),
]
