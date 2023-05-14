# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import re

import rdflib
import shortuuid
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from passlib.hash import pbkdf2_sha256

from .schema import AS, LDP, VOC, RDF, SEC

USERPART_RE = r"[a-z0-9.~_!$&'()*+,;=-]([a-z0-9.~_!$&'()*+,;=-]|%[0-9a-f]{2})*"
# FIXME support IP addresses
HOST_RE = r"([a-z0-9.~_!$&'()*+,;=-]|%[0-9a-f]+)*"
ACCT_RE = f"{USERPART_RE}@{HOST_RE}"

# FIXME should we use something else than users?
LOCAL_ACTOR_URI_FORMAT = "https://{domain}/users/{local}"


class ActivityPubActorMixin:
    @staticmethod
    def is_valid_acct(acct: str) -> bool:
        if re.match(ACCT_RE, acct.removeprefix("acct:")) is None:
            return False
        else:
            return True

    def generate_actor_keypair(self, subject: rdflib.URIRef, force: bool = False) -> rdflib.URIRef:
        self._logger.info("Generating actor keypair for %s", subject)

        if not isinstance(subject, rdflib.URIRef):
            subject = rdflib.URIRef(subject)

        # Verify that the actor does not have a key yet
        if (subject, SEC.publicKey, None) in self:
            if force:
                self._logger.warning("%s already has a key, but replacement forced", subject)
            else:
                raise TypeError(f"Actor {subject} already has a key")

        key_pair = rsa.generate_private_key(
            backend=crypto_default_backend(), public_exponent=65537, key_size=2048
        )
        private_key = key_pair.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            # FIXME support encryption with a configured passphrase
            crypto_serialization.NoEncryption(),
        ).decode("utf-8")
        public_key = (
            key_pair.public_key()
            .public_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        key_id = shortuuid.uuid()
        key_subject = subject + f"#{key_id}"
        self._logger.info("Key ID %s generated", key_subject)

        self._logger.debug("Adding attributes for key %s", key_subject)
        self.set((key_subject, SEC.owner, subject))
        self.set((key_subject, SEC.publicKeyPem, rdflib.Literal(public_key)))
        self.set((key_subject, SEC.privateKeyPem, rdflib.Literal(private_key)))

        self._logger.debug("Linking key to actor %s", subject)
        self.set((subject, SEC.publicKey, key_subject))
        self.set((subject, SEC.privateKey, key_subject))

        return key_subject

    def create_actor_from_acct(self, acct: str, name: str, type_: str, force: bool) -> str:
        # FIXME support auto-assigned ID, probably using alsoKnownAs
        self._logger.debug("Creating actor from account name %s", acct)

        acct = acct.removeprefix("acct:")

        if not self.is_valid_acct(acct):
            raise ValueError(f"Account name {acct} is invalid.")

        local, domain = acct.split("@")
        actor_type = AS[type_.title()]
        actor_uri = rdflib.URIRef(LOCAL_ACTOR_URI_FORMAT.format(local=local, domain=domain))

        self.create_actor(actor_uri, actor_type, username=local, name=name, force=force)

        self._logger.debug("Writing link between %s and %s for Webfinger", acct, actor_uri)
        self.add((actor_uri, AS.alsoKnownAs, rdflib.URIRef(f"acct:{acct}")))
        self.add((rdflib.URIRef(f"acct:{acct}"), AS.alsoKnownAs, actor_uri))

        self._logger.info("Created actor for %s with ID %s", acct, actor_uri)
        return actor_uri

    def create_actor(
        self,
        actor_uri: rdflib.URIRef,
        actor_type: rdflib.URIRef,
        username: str | None = None,
        name: str | None = None,
        force: bool = False,
    ):
        if not self.is_local_prefix(str(actor_uri)) and not force:
            raise ValueError(f"{actor_uri} is not in a local prefix")

        inbox_uri = rdflib.URIRef(f"{actor_uri}/inbox")
        outbox_uri = rdflib.URIRef(f"{actor_uri}/outbox")
        following_uri = rdflib.URIRef(f"{actor_uri}/following")
        followers_uri = rdflib.URIRef(f"{actor_uri}/followers")

        for uri in (actor_uri, inbox_uri, outbox_uri, following_uri, followers_uri):
            if (rdflib.URIRef(uri), None, None) in self and not force:
                raise ValueError(f"{uri} already exists on graph")

        self.create_collection(inbox_uri, ordered=True)
        self.create_collection(outbox_uri, ordered=True)
        self.create_collection(following_uri)
        self.create_collection(followers_uri)

        self._logger.debug("Writing attributes and links for actor %s", actor_uri)
        self.set((actor_uri, RDF.type, actor_type))
        if username:
            self.set((actor_uri, AS.preferredUsername, rdflib.Literal(username)))
        if name:
            self.set((actor_uri, AS.name, rdflib.Literal(name)))
        self.set((actor_uri, LDP.inbox, inbox_uri))
        self.set((actor_uri, AS.outbox, outbox_uri))
        self.set((actor_uri, AS.following, following_uri))
        self.set((actor_uri, AS.followers, followers_uri))

        self.generate_actor_keypair(actor_uri)

        self._logger.debug("Linking prefix endpoints node to actor")
        endpoints_node = self.get_prefix_endpoints_node(self.get_url_prefix(actor_uri), create=True)
        self.set((actor_uri, AS.endpoints, endpoints_node))

    def set_actor_password(self, actor: str, password: str) -> None:
        hash = pbkdf2_sha256.hash(password)
        self.set((rdflib.URIRef(actor), VOC.hashedPassword, rdflib.Literal(hash)))

    def verify_actor_password(self, actor: str, password: str) -> bool:
        if isinstance(actor, str):
            actor = rdflib.URIRef(actor)
        hash = self.value(subject=actor, predicate=VOC.hashedPassword)
        if hash is None:
            return False
        return pbkdf2_sha256.verify(password, str(hash))

    def get_public_key_by_id(self, id_: rdflib.term.Identifier | str) -> str | None:
        if isinstance(id_, str):
            id_ = rdflib.URIRef(id_)
        pem = self.value(subject=id_, predicate=SEC.publicKeyPem, default="")
        return str(pem) or None

    def get_public_key(self, actor: rdflib.term.Identifier | str) -> tuple[str | None, str | None]:
        if isinstance(actor, str):
            actor = rdflib.URIRef(actor)
        id_ = self.value(subject=actor, predicate=SEC.publicKey)
        if id_ is None:
            return None, None

        pem = self.get_public_key_by_id(id_)
        return str(id_), str(pem)

    def get_private_key_by_id(self, id_: rdflib.term.Identifier | str) -> str | None:
        if isinstance(id_, str):
            id_ = rdflib.URIRef(id_)
        pem = self.value(subject=id_, predicate=SEC.privateKeyPem, default="")
        return str(pem) or None

    def get_actor_by_key_id(self, id_: rdflib.term.Identifier | str) -> str | None:
        if isinstance(id_, str):
            id_ = rdflib.URIRef(id_)
        actor = self.value(subject=id_, predicate=SEC.owner | SEC.controller, default="")
        return str(actor) or None

    def get_private_key(self, actor: rdflib.term.Identifier | str) -> tuple[str | None, str | None]:
        id_ = self.value(subject=actor, predicate=SEC.privateKey)
        if id_ is None:
            return None, None

        pem = self.get_private_key_by_id(id_)

        return str(id_), str(pem)

    def get_actor_inbox(self, actor: rdflib.term.Identifier | str) -> rdflib.URIRef | None:
        return self.value(subject=actor, predicate=LDP.inbox)

    def get_actor_outbox(self, actor: rdflib.term.Identifier | str) -> rdflib.URIRef | None:
        return self.value(subject=actor, predicate=AS.outbox)


__all__ = ["ActivityPubActorMixin"]
