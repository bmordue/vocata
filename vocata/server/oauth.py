from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

_ENDPOINT_MAP = {
    "oauthAuthorizationEndpoint": "authorization_endpoint",
    "oauthTokenEndpoint": "token_endpoint",
    "oauthRegistrationEndpoint": "registration_endpoint",
}


class OAuthMetadataEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        prefix = str(request.base_url).rstrip("/")

        data = {}

        for endpoint, claim in _ENDPOINT_MAP.items():
            url = request.state.graph.get_prefix_endpoint(prefix, endpoint)
            if url:
                data[claim] = url

        if not data:
            return JSONResponse({"error": "OAuth endpoints not configured"}, 404)

        data["issuer"] = prefix

        return JSONResponse(data)
