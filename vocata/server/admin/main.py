import typing as t
from urllib.parse import urlparse

# from starlette.requests import Request
from starlette.endpoints import HTTPEndpoint
from starlette.responses import RedirectResponse
from starlette.routing import Route, Mount

import logging

if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


class AdminDashboardEndpoint(HTTPEndpoint):
    async def get(self, request) -> "TemplateResponse":
        # test if actor was already identified in the session

        return request.state.templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
            },
        )


routes = [Route("/", endpoint=AdminDashboardEndpoint, name="dashboard")]
