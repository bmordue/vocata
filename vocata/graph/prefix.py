# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from urllib.parse import urljoin, urlparse

import rdflib
import shortuuid

from ..util.types import coerce_uris
from .schema import AS, RDF, VOC


class ActivityPubPrefixMixin:
    @staticmethod
    @coerce_uris
    def get_url_prefix(uri: str) -> rdflib.URIRef:
        url = urlparse(uri)
        if not url.scheme or not url.netloc:
            raise ValueError(f"{uri} is missing either scheme or netloc")
        return rdflib.URIRef(f"{url.scheme}://{url.netloc}")

    @coerce_uris
    def is_local_prefix(self, prefix: rdflib.URIRef) -> bool:
        uri = self.get_url_prefix(prefix)
        return (uri, VOC.isLocal, rdflib.Literal(True)) in self

    @coerce_uris
    def set_local_prefix(
        self, prefix: rdflib.URIRef, is_local: bool = True, reset_endpoints: bool = True
    ):
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
                self.add((uri, AS.alsoKnownAs, rdflib.URIRef(f"acct:{domain}@{domain}")))

            self._logger.debug("Ensuring existence of prefix endpoints")
            if reset_endpoints:
                self.reset_prefix_endpoints(prefix)
            else:
                self.get_prefix_endpoints_node(prefix, create=True)

    @coerce_uris
    def get_prefix_endpoints_node(
        self, prefix: rdflib.URIRef, create: bool = False
    ) -> rdflib.term.BNode | None:
        endpoints_node = self.value(subject=prefix, predicate=AS.endpoints)
        if endpoints_node is None and create:
            endpoints_node = self.reset_prefix_endpoints(prefix)
        return endpoints_node

    @coerce_uris
    def get_prefix_endpoint(self, prefix: rdflib.URIRef, endpoint: str) -> str:
        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            return None

        url = self.value(subject=endpoints_node, predicate=AS[endpoint], default="")
        return str(url) or None

    @coerce_uris
    def reset_prefix_endpoints(
        self, prefix: rdflib.URIRef, endpoints: dict[str, str] | None = None
    ) -> rdflib.term.BNode:
        if not self.is_local_prefix(prefix):
            raise ValueError(f"{prefix} is not a local prefix")
        self._logger.info("Resetting/creating endpoints node for prefix %s", prefix)

        endpoints_node = self.get_prefix_endpoints_node(prefix)
        if endpoints_node is None:
            endpoints_node = rdflib.term.BNode()
            self.set((rdflib.URIRef(prefix), AS.endpoints, endpoints_node))

        self.remove((endpoints_node, None, None))

        if endpoints is not None:
            for endpoint, url in endpoints.items():
                self.add((endpoints_node, AS[endpoint], rdflib.Literal(url)))

        return endpoints_node

    @coerce_uris
    def generate_id(
        self, subject: rdflib.term.Node, prefix: str, fallback_ns: str = "Object"
    ) -> rdflib.URIRef:
        type_ = self.value(subject=subject, predicate=RDF.type) or fallback_ns

        uri_ns = type_.fragment.lower()
        uri_name = shortuuid.uuid()

        new_id = urljoin(urljoin(prefix, f"/{uri_ns}/"), uri_name)
        return rdflib.URIRef(new_id)

    @coerce_uris
    def reassign_id(
        self, subject: rdflib.term.Node, prefix: str, fallback_ns: str = "Object"
    ) -> rdflib.URIRef:
        new_id = self.generate_id(subject, prefix, fallback_ns)
        self._logger.debug("Replacing subjects with ID %s with %s", subject, new_id)

        for _, p, o in self.triples((subject, None, None)):
            self.add((new_id, p, o))
            self.remove((subject, p, o))

        for s, p, _ in self.triples((None, None, subject)):
            self.add((s, p, new_id))
            self.remove((s, p, subject))

        return new_id


__all__ = ["ActivityPubPrefixMixin"]
