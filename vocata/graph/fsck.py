# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Callable

import rdflib

from .schema import AS, RDF, VOC

_fsck_checks: set[Callable[[bool], int]] = set()


def fsck_check(check_fn: Callable[[bool], int]) -> Callable[[bool], int]:
    _fsck_checks.add(check_fn)
    return check_fn


class GraphFsckMixin:
    def fsck(self, fix: bool = False) -> bool:
        self._logger.info("Checking%s graph schema", " and fixing" if fix else "")

        problems = 0
        for check_fn in _fsck_checks:
            self._logger.info("Check: %s", check_fn.__doc__)
            problems += check_fn(self, fix=fix)
        return problems > 0

    @fsck_check
    def _fsck_webfingerhref(self, fix: bool = False) -> int:
        """Use AS.alsoKnownAs on actor to link webfinger acct."""
        problems = 0
        for s, p, o in self.triples((None, VOC.webfingerHref, None)):
            self._logger.warning("%s has webfignerHref, should be alsoKnownAs", s)
            problems += 1
            if fix:
                self._logger.info("Replacing webfingerHref for %s with alsoKnownAs on %s", s, o)
                target = rdflib.URIRef(str(o))
                self.add((target, AS.alsoKnownAs, s))
                self.add((s, AS.alsoKnownAs, target))
                self.remove((s, p, o))
                problems -= 1
        return problems

    @fsck_check
    def _fsck_prefix_service_actor(self, fix: bool = False) -> int:
        """Local prefixes should be a Service actor."""
        problems = 0
        for s in self.subjects(predicate=VOC.isLocal, object=rdflib.Literal(True), unique=True):
            if (s, RDF.type, AS.Service) not in self:
                self._logger.warning("Prefix %s has no Service actor", s)
                problems += 1
                if fix:
                    from urllib.parse import urlparse

                    domain = urlparse(str(s)).netloc
                    self.create_actor(
                        s,
                        AS.Service,
                        username=domain,
                        name=f"Vocata instance at {domain}",
                        force=True,
                    )
                    self.add((s, AS.alsoKnownAs, rdflib.URIRef(f"acct:{domain}@{domain}")))
                    problems -= 1
        return problems

    @fsck_check
    def _fsck_alsoknownas_symmetric(self, fix: bool = False) -> int:
        """AS.alsoKnownAs must be symmetric"""
        problems = 0
        for s, p, o in self.triples((None, AS.alsoKnownAs, None)):
            if (o, p, s) not in self:
                if not self.is_local_prefix(o) and not o.startswith("acct:"):
                    continue

                self._logger.warning(
                    "%s alsoKnownAs %s is not symmetric",
                )
                problems += 1
                if fix:
                    self._logger.info("Addins %s alsoKnownAs %s", o, s)
                    self.add((o, AS.alsoKnownAs, s))
                    problems -= 1
        return problems
