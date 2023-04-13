import rdflib

from .schema import VOC, SEC


class ActivityPubActorMixin:
    def get_actor_uri_by_acct(self, acct: str) -> str | None:
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
