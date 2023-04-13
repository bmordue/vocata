from importlib.metadata import metadata

from requests import Response, Session
from requests_http_message_signatures import HTTPSignatureHeaderAuth

CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class ActivityPubFederationMixin:
    _http_session: Session | None = None

    @property
    def _user_agent(self):
        meta = metadata("Vocata")
        return f"{meta['Name']}/{meta['Version']}"

    @property
    def http_session(self) -> Session:
        if self._http_session is None:
            self._http_session = Session()
            self._http_session.headers = {
                "User-Agent": self._user_agent,
                "Accept": ", ".join(
                    [CONTENT_TYPE, "application/activity+json;q=0.9", "application/json;q=0.8"]
                ),
            }
        return self._http_session

    def _request(self, method: str, target: str, actor: str, data: dict | None = None) -> Response:
        if method not in ["GET", "POST"]:
            raise ValueError("Only GET and POST are valid HTTP methods for ActivityPub")

        headers = {}
        auth = None
        if method == "POST":
            headers["Content-Type"] = CONTENT_TYPE

            priv_id, priv_pem = self.get_private_key(actor)
            auth = HTTPSignatureHeaderAuth(
                algorithm="rsa-sha256",
                key=priv_pem.encode("utf-8"),
                key_id=priv_id,
                headers=["(request-target)", "host", "date", "digest"],
            )

        return self.http_session.request(method, target, headers=headers, json=data, auth=auth)

    def pull(self, subject: str, actor: str) -> Response:
        response = self._request("GET", subject, actor)
        response.raise_for_status()

        if response.status_code == 200:
            self.add_jsonld(response.json())

        return response

    def push_to(self, target: str, subject: str, actor: str) -> Response:
        # FIXME do we really want to retrieve as `actor` here?
        data = self.activitystream_cbd(subject, actor).to_activitystream(subject)
        if not data:
            # FIXME do we want to use this for re-pushing as well?
            #  in that case, we should pull first
            raise KeyError(f"{subject} is unknown")

        # FIXME test for locally owned targets here
        return self._request("POST", target, actor, data)
