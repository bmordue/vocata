from urllib.parse import urljoin, urlparse

import rdflib

from .schema import AS, VOC

_DEFAULT_ENDPOINTS = {
    "proxyUrl": "/_functional/proxy",
    "oauthAuthorizationEndpoint": "/_functional/oauth/authorization",
    "oauthTokenEndpoint": "/_functional/oauth/token",
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

    def set_local_prefix(self, prefix: str, is_local: bool = True):
        uri = self.get_url_prefix(prefix)
        self._logger.info("Declaring %s a %slocal prefix", uri, "" if is_local else "(non-)")
        self.set((uri, VOC.isLocal, rdflib.Literal(is_local)))

        if is_local:
            self._logger.debug("Ensuring existence of prefix endpoints")
            self.get_prefix_endpoints_node(prefix, create=True)

    def get_prefix_endpoints_node(
        self, prefix: str, create: bool = False
    ) -> rdflib.term.BNode | None:
        endpoints_node = self.value(subject=prefix, predicate=AS.endpoints)
        if endpoints_node is None and create:
            endpoints_node = self.reset_prefix_endpoints(prefix)
        return endpoints_node

    def get_prefix_endpoint(self, prefix: str, endpoint: str) -> str:
        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            return None

        url = self.value(subject=endpoints_node, predicate=AS[endpoint])
        if url is None:
            return None

        return str(url)

    def set_prefix_endpoint(self, prefix: str, endpoint: str, url: str):
        if not self.is_local_prefix(prefix):
            raise ValueError(f"{prefix} is not a local prefix")

        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            self.reset_prefix_endpoints(prefix)

        self._logger.info("Setting endpoint %s of %s to %s", endpoint, prefix, url)
        self.set((endpoints_node, AS[endpoint], rdflib.Literal(url)))

    def reset_prefix_endpoints(self, prefix: str) -> rdflib.term.BNode:
        if not self.is_local_prefix(prefix):
            raise ValueError(f"{prefix} is not a local prefix")
        self._logger.info("Resetting/creating endpoints node for prefix %s", prefix)

        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            endpoints_node = rdflib.term.BNode()
            self.set((rdflib.URIRef(prefix), AS.endpoints, endpoints_node))

        self.remove((endpoints_node, None, None))
        for endpoint, url_path in _DEFAULT_ENDPOINTS.items():
            self.set_prefix_endpoint(prefix, endpoint, urljoin(prefix, url_path))

        return endpoints_node


__all__ = ["ActivityPubPrefixMixin"]
