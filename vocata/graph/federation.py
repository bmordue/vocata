from base64 import b64encode
from email.utils import formatdate
from hashlib import sha256
from importlib.metadata import metadata
from typing import ClassVar, TYPE_CHECKING

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from requests import Request, Response, Session
from requests.auth import AuthBase

if TYPE_CHECKING:
    from .graph import ActivityPubGraph

CONTENT_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'


class HTTPSignatureAuth(AuthBase):
    _HEADERS: ClassVar[list[str]] = ["(request-target)", "host", "date", "digest"]

    def __init__(
        self, graph: "ActivityPubGraph", actor: str | None = None, key_id: str | None = None
    ):
        if actor and key_id:
            raise TypeError("Only one of actor or key_id must be provided.")

        self._graph = graph
        if actor:
            self._key_id, _ = self._graph.get_private_key(actor)
            if not self._key_id:
                raise ValueError(f"No known key ID for {actor}")
        else:
            self._key_id = key_id

        # FIXME enable once we can distinguish local and remote
        # self._graph.pull(self._key_id)

        self._private_key_pem = self._graph.get_private_key_by_id(self._key_id)
        self._public_key_pem = self._graph.get_public_key_by_id(self._key_id)

        if self._private_key_pem:
            self._private_key = crypto_serialization.load_pem_private_key(
                self._private_key_pem.encode("utf-8"),
                # FIXME support a configurable password
                password=None,
                backend=crypto_default_backend(),
            )
        else:
            self._private_key = None

        if self._public_key_pem:
            self._public_key = crypto_serialization.load_pem_public_key(
                self._public_key_pem.encode("utf-8"), backend=crypto_default_backend()
            )
        else:
            self._public_key = None

    def __call__(self, request: Request) -> Request:
        if not self._private_key:
            raise ValueError(f"Private key {self._key_id} is unknown")

        signature_data = []
        used_headers = []
        for header in self._HEADERS:
            if header not in request.headers:
                if header.lower() == "date":
                    request.headers["Date"] = formatdate(timeval=None, localtime=False, usegmt=True)
                elif header.lower() == "digest" and request.body is not None:
                    request.headers["Digest"] = "SHA-256=" + b64encode(
                        sha256(request.body).digest()
                    ).decode("utf-8")

                if header.lower() == "(request-target)":
                    method = request.method.lower()
                    path = request.path_url
                    signature_data.append(f"(request-target): {method} {path}")
                    used_headers.append("(request-target)")
                elif header in request.headers:
                    name = header.lower()
                    value = request.headers[header]
                    signature_data.append(f"{name}: {value}")
                    used_headers.append(name)

        signature_text = "\n".join(signature_data)
        signature = b64encode(
            self._private_key.sign(
                signature_text.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256()
            )
        ).decode("utf-8")
        headers = " ".join(used_headers)
        signature_fields = [
            f'keyId="{self._key_id}"',
            'algorithm="rsa-sha256"',
            f'headers="{headers}"',
            f'signature="{signature}"',
        ]
        signature_header = ",".join(signature_fields)

        request.headers["Signature"] = signature_header
        return request


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
            auth = HTTPSignatureAuth(self, actor)

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
