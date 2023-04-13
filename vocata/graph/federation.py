from base64 import b64encode
from email.utils import formatdate
from hashlib import sha256
from importlib.metadata import metadata
from pprint import pformat
from typing import ClassVar, TYPE_CHECKING
from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from requests import Request, Response, Session
from requests.auth import AuthBase
from requests.exceptions import JSONDecodeError

from .authz import HAS_ACTOR, HAS_TRANSIENT_AUDIENCE, HAS_TRANSIENT_INBOXES, PUBLIC_ACTOR

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
            self._graph._logger.debug("Found key ID %s for %s", self._key_id, actor)
        else:
            self._key_id = key_id
        self._graph._logger.debug("Creating HTTP signer with key ID %s", self._key_id)

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
            self._graph._logger.debug("Private key with ID %s found", self._key_id)
        else:
            self._private_key = None
            self._graph._logger.debug("Private key with ID %s not found", self._key_id)

        if self._public_key_pem:
            self._public_key = crypto_serialization.load_pem_public_key(
                self._public_key_pem.encode("utf-8"), backend=crypto_default_backend()
            )
            self._graph._logger.debug("Public key with ID %s not found", self._key_id)
        else:
            self._public_key = None
            self._graph._logger.warning("Public key with ID %s not found", self._key_id)

    def __call__(self, request: Request) -> Request:
        self._graph._logger.debug(
            "Signing header for %s request to %s", request.method, request.url
        )
        self._graph._logger.debug("Request headers before signing: %s", pformat(request.headers))

        if not self._private_key:
            raise ValueError(f"Private key {self._key_id} is unknown")

        signature_data = []
        used_headers = []
        for header in self._HEADERS:
            if header not in request.headers:
                if header.lower() == "date":
                    self._graph._logger.debug("Adding Date header to request")
                    request.headers["Date"] = formatdate(timeval=None, localtime=False, usegmt=True)
                elif header.lower() == "digest" and request.body is not None:
                    self._graph._logger.debug("Adding Digest header to request")
                    request.headers["Digest"] = "SHA-256=" + b64encode(
                        sha256(request.body).digest()
                    ).decode("utf-8")
                elif header.lower() == "host":
                    self._graph._logger.debug("Adding Host header to request")
                    request.headers["Host"] = urlparse(request.url).netloc

            if header.lower() == "(request-target)":
                self._graph._logger.debug("Adding (request-target) pseudo-header to signature")
                method = request.method.lower()
                path = request.path_url
                signature_data.append(f"(request-target): {method} {path}")
                used_headers.append("(request-target)")
            elif header in request.headers:
                self._graph._logger.debug("Adding %s header to signature", header)
                name = header.lower()
                value = request.headers[header]
                signature_data.append(f"{name}: {value}")
                used_headers.append(name)
            else:
                self._graph._logger.debug("Header %s not found, skipping", header)

        signature_text = "\n".join(signature_data)
        self._graph._logger.debug("Signing header: %s", signature_text)
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
        self._graph._logger.debug("Created signature header %s", signature_header)

        request.headers["Signature"] = signature_header
        self._graph._logger.debug("Request headers after signing: %s", pformat(request.headers))

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
            self._logger.debug("Creating new HTTP client session")
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

        self._logger.debug("Preparing new %s request to %s as %s", method, target, actor)

        headers = {}
        auth = None
        if method == "POST":
            headers["Content-Type"] = CONTENT_TYPE
            auth = HTTPSignatureAuth(self, actor)
            self._logger.debug("Enabled HTTP signatures for request")

        res = self.http_session.request(method, target, headers=headers, json=data, auth=auth)
        if res.status_code >= 400:
            try:
                error = res.json()
                self._logger.error("Request failed with error: %s", pformat(error))
            except JSONDecodeError:
                error = res.text
                self._logger.error("Request failed with error: %s", error)

        return res

    def pull(self, subject: str, actor: str = PUBLIC_ACTOR) -> tuple[bool, Response]:
        # FIXME distinguish between local and remote
        self._logger.info("Pulling %s from remote", subject)
        response = self._request("GET", subject, actor)

        if response.status_code == 200:
            self._logger.debug("Successfully pulled %s", subject)
            self.add_jsonld(response.json())
        else:
            self._logger.error("Error pulling %s", subject)

        return response.status_code < 400, response

    def push_to(self, target: str, subject: str, actor: str) -> tuple[bool, Response]:
        self._logger.info("Pushing %s to remote %s", subject, target)
        # FIXME do we really want to retrieve as `actor` here?
        data = self.activitystream_cbd(subject, actor).to_activitystream(subject)
        if not data:
            # FIXME do we want to use this for re-pushing as well?
            #  in that case, we should pull first
            raise KeyError(f"{subject} is unknown")

        # FIXME test for locally owned targets here
        response = self._request("POST", target, actor, data)

        if response.status_code < 400:
            self._logger.debug("Successfully pushed %s to %s", subject, target)
        else:
            self._logger.error("Failed to push %s to %s", subject, target)

        return response.status_code < 400, response

    def get_all_targets(self, subject: str) -> set[str]:
        # FIXME we need to resolve for an actor!
        self._logger.debug("Resolving inboxes for audience of %s", subject)

        # FIXME enable once we can distinguish local and remote
        # self.pull(subject)

        audience = set()
        for _ in range(3):
            new_audience = set(
                map(str, self.objects(subject=subject, predicate=HAS_TRANSIENT_AUDIENCE))
            )
            if audience == new_audience:
                break
            for recipient in new_audience:
                if recipient != PUBLIC_ACTOR and recipient not in audience:
                    self.pull(recipient)
            audience = new_audience

        inboxes = self.objects(subject=subject, predicate=HAS_TRANSIENT_INBOXES)
        inbox_set = set(map(str, inboxes))
        self._logger.debug("Resolved %s to %d inboxes", subject, len(inbox_set))

        return inbox_set

    def push(self, subject: str) -> tuple[set[Response], set[Response]]:
        self._logger.info("Pushing %s to its audience", subject)

        actor = self.value(subject=subject, predicate=HAS_ACTOR)
        if not actor:
            raise TypeError(f"{subject} has no actor; can only push activities")
        self._logger.debug("Actor for %s is %s", subject, actor)

        targets = self.get_all_targets(subject)

        succeeded = set()
        failed = set()
        for target in targets:
            success, res = self.push_to(target, subject, actor)
            if success:
                succeeded.add(res)
            else:
                failed.add(res)

        return succeeded, failed
