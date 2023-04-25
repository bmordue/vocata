from base64 import b64decode, b64encode
from email.utils import formatdate
from hashlib import sha256
from pprint import pformat
from time import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from requests.auth import AuthBase
from requests import Request

if TYPE_CHECKING:
    from .graph import ActivityPubGraph


class HTTPSignatureAuth(AuthBase):
    _headers: list[str] | None = None

    _key_id: str | None = None
    _public_key_pem: str | None = None
    _public_key: PublicKeyTypes | None = None
    _private_key_pem: str | None = None
    _private_key: PrivateKeyTypes | None = None

    def __init__(
        self,
        graph: "ActivityPubGraph",
        headers: list[str],
        actor: str | None = None,
        key_id: str | None = None,
    ):
        if actor and key_id:
            raise TypeError("Only one of actor or key_id must be provided.")

        self._headers = headers

        self._graph = graph
        if actor:
            key_id, _ = self._graph.get_public_key(actor)
            if key_id:
                self._graph._logger.debug("Found key ID %s for %s", self._key_id, actor)
            else:
                self._graph._logger.warning("No known key ID for %s", actor)
        if key_id:
            self._set_key(key_id)
        self._graph._logger.debug("Creating HTTP signer with key ID %s", self._key_id)

    def _set_key(self, key_id: str):
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
            self._graph._logger.debug("Private key with ID %s found", self._key_id)
        else:
            self._private_key = None
            self._graph._logger.debug("Private key with ID %s not found", self._key_id)

        if self._public_key_pem:
            self._public_key = crypto_serialization.load_pem_public_key(
                self._public_key_pem.encode("utf-8"), backend=crypto_default_backend()
            )
            self._graph._logger.debug("Public key with ID %s found", self._key_id)
        else:
            self._public_key = None
            self._graph._logger.warning("Public key with ID %s not found", self._key_id)

    @staticmethod
    def get_signature_fields(signature_header: str) -> dict[str, str]:
        signature_fields = {}
        for field in signature_header.split(","):
            name, value = field.split("=", 1)
            if name in signature_fields:
                raise KeyError(f"Duplicate field {name} in signature")
            signature_fields[name] = value.strip('"')
        return signature_fields

    @classmethod
    def from_signed_request(cls, request: Request, pull: bool = True) -> str:
        signature_text = None
        if "Signature" in request.headers:
            signature_text = request.headers["Signature"]
        elif "Authorization" in request.headers:
            scheme, parameters = request.headers["Authorization"].split(" ", 1)
            if scheme.lower() == "signature":
                signature_text = parameters
        if signature_text is None:
            raise KeyError("No signature found in headers")
        signature_fields = cls.get_signature_fields(signature_text)

        if "keyId" not in signature_fields:
            raise KeyError("keyId missing in signature")
        if "signature" not in signature_fields:
            raise KeyError("signature missing")

        if "created" in signature_fields:
            created_time = int(signature_fields["created"])
            if created_time > time.time():
                raise ValueError("created time is in the future")

        if "expires" in signature_fields:
            expires_time = int(signature_fields["expires"])
            if expires_time < time.time():
                raise ValueError("expires time is in the past")

        if "headers" in signature_fields:
            headers = signature_fields["headers"].split(" ")
        else:
            headers = ["(created)"]

        if pull:
            success, response = request.state.graph.pull(signature_fields["keyId"])
            if not success:
                raise RuntimeError(f"Could not retrieve actor key: {response.text}")

        return cls(request.state.graph, headers, key_id=signature_fields["keyId"])

    def synthesize_headers(self, request: Request) -> None:
        for header in self._headers:
            if header not in request.headers:
                if header.lower() == "date":
                    request.headers["Date"] = formatdate(timeval=None, localtime=False, usegmt=True)
                elif header.lower() == "digest" and request.body is not None:
                    request.headers["Digest"] = "SHA-256=" + b64encode(
                        sha256(request.body).digest()
                    ).decode("utf-8")
                elif header.lower() == "host":
                    request.headers["Host"] = urlparse(request.url).netloc

    def construct_signature_data(self, request: Request) -> tuple[str, str]:
        signature_data = []
        used_headers = []
        for header in self._headers:
            # FIXME support created and expires pseudo-headers
            if header.lower() == "(request-target)":
                method = request.method.lower()
                if hasattr(request, "path_url"):
                    path = request.path_url
                else:
                    path = request.url.path
                signature_data.append(f"(request-target): {method} {path}")
                used_headers.append("(request-target)")
            elif header in request.headers:
                name = header.lower()
                value = request.headers[header]
                signature_data.append(f"{name}: {value}")
                used_headers.append(name)
            else:
                print(self._headers)
                raise KeyError("Header %s not found", header)

        signature_text = "\n".join(signature_data)
        headers_text = " ".join(used_headers)
        return signature_text, headers_text

    async def verify_request(self, request: Request) -> str:
        signature_text, headers_text = self.construct_signature_data(request)

        if headers_text != " ".join(self._headers):
            raise ValueError("Headers listed in signature mismatch with request")

        signature_fields = self.get_signature_fields(request.headers["Signature"])
        signature = b64decode(signature_fields["signature"].encode("utf-8"))
        # FIXME determine modes from signature data and/or key
        self._public_key.verify(
            signature, signature_text.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256()
        )

        if "digest" in self._headers and request.body is not None:
            body = await request.body()
            digest = "SHA-256=" + b64encode(sha256(body).digest()).decode("utf-8")
            if request.headers["Digest"] != digest:
                raise ValueError("Digest of body is invalid")

        return signature_fields["keyId"]

    def __call__(self, request: Request) -> Request:
        self._graph._logger.debug(
            "Signing header for %s request to %s", request.method, request.url
        )
        self._graph._logger.debug("Request headers before signing: %s", pformat(request.headers))

        if not self._private_key:
            self._graph._logger.error("Private key unknown. Skipping signature.")
            return request

        self.synthesize_headers(request)
        signature_text, headers_text = self.construct_signature_data(request)

        self._graph._logger.debug("Signing header: %s", signature_text)
        signature = b64encode(
            self._private_key.sign(
                signature_text.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256()
            )
        ).decode("utf-8")
        signature_fields = [
            f'keyId="{self._key_id}"',
            'algorithm="rsa-sha256"',
            f'headers="{headers_text}"',
            f'signature="{signature}"',
        ]
        signature_header = ",".join(signature_fields)
        self._graph._logger.debug("Created signature header %s", signature_header)

        request.headers["Signature"] = signature_header
        self._graph._logger.debug("Request headers after signing: %s", pformat(request.headers))

        return request
