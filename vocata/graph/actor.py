import re

import rdflib
import shortuuid
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

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
        if re.match(ACCT_RE, acct) is None:
            return False
        else:
            return True

    def generate_actor_keypair(self, subject: rdflib.URIRef, force: bool = False) -> rdflib.URIRef:
        self._logger.info("Generating actor keypair for %s", subject)

        if not isinstance(subject, rdflib.URIRef):
            subject = rdflib.URIRef(subject)

        # Verify that the actor does not have a key yet
        if self.value(subject=subject, predicate=SEC.publicKey):
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

    def create_actor_from_acct(self, acct: str, name: str, type_: str) -> str:
        self._logger.debug("Creating actor from account name %s", acct)

        if not self.is_valid_acct(acct):
            raise ValueError(f"Account name {acct} is invalid.")

        local, domain = acct.split("@")
        actor_type = AS[type_.title()]

        actor_uri = rdflib.URIRef(LOCAL_ACTOR_URI_FORMAT.format(local=local, domain=domain))
        inbox_uri = rdflib.URIRef(f"{actor_uri}/inbox")
        outbox_uri = rdflib.URIRef(f"{actor_uri}/outbox")
        following_uri = rdflib.URIRef(f"{actor_uri}/following")
        followers_uri = rdflib.URIRef(f"{actor_uri}/followers")

        for uri in (actor_uri, inbox_uri, outbox_uri, following_uri, followers_uri):
            if (rdflib.URIRef(uri), None, None) in self:
                raise ValueError(f"{uri} already exists on graph")

        self._logger.debug("Creating collection %s", inbox_uri)
        self.set((inbox_uri, RDF.type, AS.OrderedCollection))
        self.set((inbox_uri, AS.totalItems, rdflib.Literal(0)))
        self._logger.debug("Creating collection %s", outbox_uri)
        self.set((outbox_uri, RDF.type, AS.OrderedCollection))
        self.set((outbox_uri, AS.totalItems, rdflib.Literal(0)))
        self._logger.debug("Creating collection %s", following_uri)
        self.set((following_uri, RDF.type, AS.Collection))
        self.set((following_uri, AS.totalItems, rdflib.Literal(0)))
        self._logger.debug("Creating collection %s", followers_uri)
        self.set((followers_uri, RDF.type, AS.Collection))
        self.set((followers_uri, AS.totalItems, rdflib.Literal(0)))

        self._logger.debug("Writing attributes and links for actor %s", actor_uri)
        self.set((actor_uri, RDF.type, actor_type))
        self.set((actor_uri, AS.preferredUsername, rdflib.Literal(local)))
        self.set((actor_uri, AS.name, rdflib.Literal(name)))
        self.set((actor_uri, LDP.inbox, inbox_uri))
        self.set((actor_uri, AS.outbox, outbox_uri))
        self.set((actor_uri, AS.following, following_uri))
        self.set((actor_uri, AS.followers, followers_uri))

        self.generate_actor_keypair(actor_uri)

        self._logger.debug("Writing link between %s and %s for Webfinger", acct, actor_uri)
        self.set((rdflib.URIRef(f"acct:{acct}"), VOC.webfingerHref, actor_uri))

        self._logger.info("Created actor for %s with ID %s", acct, actor_uri)
        return actor_uri

    def get_actor_uri_by_acct(self, acct: str) -> str | None:
        if not acct.startswith("acct"):
            acct = f"acct:{acct}"
        uri = self.value(subject=acct, predicate=VOC.webfingerHref)
        if uri is None:
            return None
        return str(uri)

    def get_public_key_by_id(self, id_: rdflib.term.Identifier | str) -> str:
        pem = self.value(subject=id_, predicate=SEC.publicKeyPem)
        if pem is None:
            raise KeyError(f"Key {id_} not found or incomplete")

        return str(pem)

    def get_public_key(self, actor: rdflib.term.Identifier | str) -> tuple[str, str]:
        id_ = self.value(subject=actor, predicate=SEC.publicKey)
        if id_ is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        pem = self.get_public_key_by_id(id_)
        return str(id_), str(pem)

    def get_private_key_by_id(self, id_: rdflib.term.Identifier | str) -> str:
        pem = self.value(subject=id_, predicate=SEC.privateKeyPem)
        if pem is None:
            raise KeyError(f"Key {id_} not found or incomplete")

        return str(pem)

    def get_private_key(self, actor: rdflib.term.Identifier | str) -> tuple[str, str]:
        id_ = self.value(subject=actor, predicate=SEC.privateKey)
        if id_ is None:
            raise KeyError(f"Key for {actor} not found or incomplete")

        pem = self.get_private_key_by_id(id_)

        return str(id_), str(pem)


__all__ = ["ActivityPubActorMixin"]
