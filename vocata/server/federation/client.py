from importlib.metadata import metadata

from requests import Response, Session
from requests_http_message_signatures import HTTPSignatureHeaderAuth

from ...data import get_graph

CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class ActivityPubFederator:
    def __init__(self, subject: str, actor: str):
        self._graph = get_graph()

        self.subject = subject
        self.actor = actor

        self._session = Session()
        self._session.headers = {
            "User-Agent": self._user_agent,
            "Accept": CONTENT_TYPE,
        }

    @property
    def _user_agent(self):
        meta = metadata("Vocata")
        return f"{meta['Name']}/{meta['Version']}"

    def _request(self, method: str, target: str | None = None, data: dict | None = None) -> Response:
        if method not in ["GET", "POST"]:
            raise ValueError("Only GET and POST are valid HTTP methods for ActivityPub")

        headers = {}
        auth = None
        if method == "POST":
            headers["Content-Type"] = CONTENT_TYPE

            priv_id, priv_pem = self._graph.get_private_key(self.actor)
            auth = HTTPSignatureHeaderAuth(
                algorithm="rsa-sha256",
                key=priv_pem.encode("utf-8"),
                key_id=priv_id,
                headers=["(request-target)", "host", "date", "digest"]
            )

        return self._session.request(method, target, headers=headers, json=data, auth=auth)
