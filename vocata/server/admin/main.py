import typing as t

from starlette.endpoints import HTTPEndpoint

from starlette.requests import Request

from starlette.routing import Route

from ..auth import requires_auth

import logging

if t.TYPE_CHECKING:
    from starlette.templating import TemplateResponse

logger = logging.getLogger(__name__)


class AdminDashboardEndpoint(HTTPEndpoint):
    @requires_auth
    async def get(self, request: Request) -> "TemplateResponse":
        request.state.graph._logger.info("AdminDashboardEndpoint.get()")

        return request.state.templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
            },
        )


routes = [Route("/", AdminDashboardEndpoint, name="dashboard")]
