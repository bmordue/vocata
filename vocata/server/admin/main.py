# SPDX-FileCopyrightText: © 2023 Steve Ivy <steve@monkinetic.blog>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import typing as t

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.routing import Route

from ..auth import requires_auth
from .users import AdminUsersEndpoint, AdminUserEndpoint

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


routes = [
    Route("/", AdminDashboardEndpoint, name="dashboard"),
    Route("/users/{account}/edit", AdminUserEndpoint, name="users_edit"),
    Route("/users", AdminUsersEndpoint, name="users_manage"),
]
