from urllib.parse import urljoin, urlparse

import rdflib
import requests
import shortuuid

from .schema import AS, RDF, VOC

_OAUTH_METADATA_URIS = [
    ".well-known/openid-configuration",
    ".well-known/oauth-authorization-server",
]

_CLAIM_ENDPOINT_MAP = {
    "issuer": AS.oauthIssuer,
    "authorization_endpoint": AS.oauthAuthorizationEndpoint,
    "token_endpoint": AS.oauthTokenEndpoint,
    "registration_endpoint": AS.oauthRegistrationEndpoint,
    "jwks_uri": AS.oauthJWKSUri,
}


class ActivityPubPrefixMixin:
    @staticmethod
    def get_url_prefix(uri: str) -> rdflib.URIRef:
        url = urlparse(uri)
        if not url.scheme or not url.netloc:
            raise ValueError(f"{uri} is missing either scheme or netloc")
        return rdflib.URIRef(f"{url.scheme}://{url.netloc}")

    def is_local_prefix(self, prefix: str) -> bool:
        uri = self.get_url_prefix(prefix)
        return (uri, VOC.isLocal, rdflib.Literal(True)) in self

    # FIXME rethink with a clear OIDC concept
    def set_prefix_oauth_issuer(self, prefix: str, issuer: str):
        self._logger.debug("Setting OAuth issuer for %s to %s", prefix, issuer)

        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }
        config = {}
        for path in _OAUTH_METADATA_URIS:
            url = urljoin(f"{issuer}/", path)
            self._logger.debug("Trying to fetch OAuth meta-data from %s", url)
            result = requests.get(url, headers=headers)
            if result.ok:
                self._logger.debug("Found OAuth meta-data at %s", url)
                config = result.json()
                break
            self._logger.debug("No OAuth meta-data at %s", url)

        if "issuer" not in config:
            raise KeyError("No (valid) OAuth meta-data found")
        elif config["issuer"] != issuer:
            raise ValueError(
                "Issuer %s is different from expected issuer %s", config["issuer"], issuer
            )

        endpoints_node = self.get_prefix_endpoints_node(prefix, create=True)
        triples = set()
        for claim, endpoint_predicate in _CLAIM_ENDPOINT_MAP.items():
            self._logger.debug("Setting %s = %s", claim, config[claim])
            triples.add((endpoints_node, endpoint_predicate, rdflib.Literal(config[claim])))
        for triple in triples:
            self.set(triple)

    def set_local_prefix(self, prefix: str, is_local: bool = True, reset_endpoints: bool = True):
        uri = self.get_url_prefix(prefix)
        self._logger.info("Declaring %s a %slocal prefix", uri, "" if is_local else "(non-)")
        self.set((uri, VOC.isLocal, rdflib.Literal(is_local)))

        if is_local:
            if not self.is_an_actor(prefix):
                domain = urlparse(str(uri)).netloc
                self.create_actor(
                    uri,
                    AS.Service,
                    username=domain,
                    name=f"Vocata instance at {domain}",
                    force=True,
                )

            self._logger.debug("Ensuring existence of prefix endpoints")
            if reset_endpoints:
                self.reset_prefix_endpoints(prefix)
            else:
                self.get_prefix_endpoints_node(prefix, create=True)

    # FIXME rethink with a clear OIDC concept
    def get_prefix_endpoints_node(
        self, prefix: str, create: bool = False
    ) -> rdflib.term.BNode | None:
        endpoints_node = self.value(subject=prefix, predicate=AS.endpoints)
        if endpoints_node is None and create:
            endpoints_node = self.reset_prefix_endpoints(prefix)
        return endpoints_node

    # FIXME rethink with a clear OIDC concept
    def get_prefix_endpoint(self, prefix: str, endpoint: str) -> str:
        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            return None

        url = self.value(subject=endpoints_node, predicate=AS[endpoint], default="")
        return str(url) or None

    # FIXME rethink with a clear OIDC concept
    def reset_prefix_endpoints(self, prefix: str) -> rdflib.term.BNode:
        if not self.is_local_prefix(prefix):
            raise ValueError(f"{prefix} is not a local prefix")
        self._logger.info("Resetting/creating endpoints node for prefix %s", prefix)

        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            endpoints_node = rdflib.term.BNode()
            self.set((rdflib.URIRef(prefix), AS.endpoints, endpoints_node))

        self.remove((endpoints_node, None, None))

        return endpoints_node

    def generate_id(self, subject: str, prefix: str, fallback_ns: str = "Object") -> rdflib.URIRef:
        type_ = self.value(subject=subject, predicate=RDF.type) or fallback_ns

        uri_ns = type_.fragment.lower()
        uri_name = shortuuid.uuid()

        new_id = urljoin(urljoin(prefix, f"/{uri_ns}/"), uri_name)
        return rdflib.URIRef(new_id)

    def reassign_id(self, subject: str, prefix: str, fallback_ns: str = "Object") -> rdflib.URIRef:
        new_id = self.generate_id(subject, prefix, fallback_ns)
        self._logger.debug("Replacing subjects with ID %S with %s", subject, new_id)

        for _, p, o in self.triples((subject, None, None)):
            self.add((new_id, p, o))
            self.remove((subject, p, o))

        for s, p, _ in self.triples((None, None, subject)):
            self.add((s, p, new_id))
            self.remove((s, p, subject))

        return new_id


__all__ = ["ActivityPubPrefixMixin"]
