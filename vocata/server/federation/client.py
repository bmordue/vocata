from importlib.metadata import metadata

from requests import Response, Session
from requests_http_message_signatures import HTTPSignatureHeaderAuth

from ...data import ActivityPubGraph, get_graph

CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class ActivityPubFederator:
    def __init__(self, subject: str, actor: str, graph: ActivityPubGraph | None = None):
        self._graph = graph or get_graph()

        self.subject = subject
        self.actor = actor

        self._session = Session()
        self._session.headers = {
            "User-Agent": self._user_agent,
            "Accept": ", ".join([CONTENT_TYPE, "application/activity+json;q=0.9", "application/json;q=0.8"]),
        }

    @property
    def _user_agent(self):
        meta = metadata("Vocata")
        return f"{meta['Name']}/{meta['Version']}"

    def _request(self, method: str, target: str, data: dict | None = None) -> Response:
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

    def pull(self) -> Response:
        response = self._request("GET", self.subject)
        response.raise_for_status()

        if response.status_code == 200:
            self._graph.add_activitystream(response.json())

        return response

    def push_to(self, target: str) -> Response:
        # FIXME do we really want to retrieve as `actor` here?
        data = self._graph.get_single_activitystream(self.subject, self.actor)
        if not data:
            # FIXME do we want to use this for re-pushing as well?
            #  in that case, we should pull first
            raise KeyError(f"{self.subject} is unknown")

        # FIXME test for locally owned targets here
        return self._request("POST", target, data)
