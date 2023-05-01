from typing import ClassVar

from starlette.background import BackgroundTask
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..graph.authz import AccessMode, PUBLIC_ACTOR
from ..graph.federation import CONTENT_TYPE


class ActivityPubEndpoint(HTTPEndpoint):
    ACCEPT_TYPES: ClassVar[set[str]] = {CONTENT_TYPE, "application/activity+json"}

    def _check_auth(
        self, request: Request, mode: AccessMode = AccessMode.READ
    ) -> bool | tuple[int, str]:
        # Check authorization
        if request.state.graph.is_authorized(request.state.actor, request.state.subject, mode):
            return True
        elif str(request.state.actor) == str(PUBLIC_ACTOR):
            return 401, "Unauthenticated actor"
        else:
            return 403, "Unauthorized"

    async def get(self, request: Request) -> JSONResponse:
        # FIXME handle Accept header
        # FIXME use HTTP caching
        auth = self._check_auth(request, AccessMode.READ)
        if auth is not True:
            return JSONResponse({"error": auth[1]}, auth[0])

        # Retrieve the object identified by URI, passing actor for authorization
        doc = request.state.graph.activitystreams_cbd(
            request.state.subject, request.state.actor
        ).to_activitystreams(request.state.subject)

        if doc is None:
            return JSONResponse({"error": "Not found"}, 404)

        # FIXME return correct content type
        return JSONResponse(doc, media_type=CONTENT_TYPE)

    async def post(self, request: Request) -> JSONResponse:
        # FIXME handle Accept header

        # POST data must be ActivityPub
        if (
            "Content-Type" not in request.headers
            or request.headers["Content-Type"] not in self.ACCEPT_TYPES
        ):
            return JSONResponse({"error": "Wrong Content-Type"}, 415)

        # POST target must be an inbox or outbox collection
        if not request.state.graph.is_a_box(request.state.subject):
            return JSONResponse({"error": "Not an inbox or outbox"}, 405)

        auth = self._check_auth(request, AccessMode.WRITE)
        if auth is not True:
            return JSONResponse({"error": auth[1]}, auth[0])

        try:
            # FIXME workaround for early read together with https://github.com/encode/starlette/pull/1519
            request._body = request.state.body

            doc = await request.json()
            new_uri = request.state.graph.handle_activity_jsonld(
                doc, request.state.subject, request.state.actor
            )
        # FIXME properly implement exception handling
        except Exception as ex:
            # FIXME distinguish 4xx and 5xx by exception status
            return JSONResponse({"error": str(ex)}, 400)

        # Side-effects of activities are carried out afterwards
        task = BackgroundTask(
            request.state.graph.carry_out_activity,
            activity=new_uri,
            box=request.state.subject,
        )

        # FIXME return correct content type
        return JSONResponse({}, 201, headers={"Location": str(new_uri)}, background=task)


class ProxyEndpoint(ActivityPubEndpoint):
    async def post(self, request: Request) -> JSONResponse:
        if not request.state.graph.is_local_prefix(request.state.actor):
            return JSONResponse({"error": "Only authenticated local actors allowed"}, 403)

        # FIXME workaround for early read together with https://github.com/encode/starlette/pull/1519
        request._body = request.state.body
        async with request.form() as form:
            if "id" not in form:
                return JSONResponse({"error": "Must provide id parameter in body"}, 400)
            real_id = form["id"]

        # FIXME add security measures to not randomly pull stuff
        # FIXME use caching
        request.state.graph.pull(real_id, request.state.actor)

        # Once authorized, we can simply fake being authoritative for the subject ;)
        request.state.subject = real_id
        return await super().get(request)
