# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Callable

import rdflib

from .schema import AS, RDF, VOC

_fsck_checks: list[Callable[[bool], int]] = []


def fsck_check(check_fn: Callable[[bool], int]) -> Callable[[bool], int]:
    _fsck_checks.append(check_fn)
    return check_fn


class GraphFsckMixin:
    def fsck(self, fix: bool = False) -> bool:
        self._logger.info("Checking%s graph schema", " and fixing" if fix else "")

        problems = 0
        for check_fn in _fsck_checks:
            self._logger.info("Check: %s", check_fn.__doc__)
            problems += check_fn(self, fix=fix)

        if problems > 0:
            self._logger.warning("Graph schema issues detected; run `vocatactl data fsck --fix`!")
            return True
        return False

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

                self._logger.warning("%s alsoKnownAs %s is not symmetric", o, s)
                problems += 1
                if fix:
                    self._logger.info("Adding %s alsoKnownAs %s", o, s)
                    self.add((o, AS.alsoKnownAs, s))
                    problems -= 1
        return problems

    @fsck_check
    def _fsck_ordereditems_predicate(self, fix: bool = False) -> int:
        """AS.orderedItems should not exist"""
        problems = 0
        subjects = set()
        for s, p, o in self.triples((None, AS.orderedItems, None)):
            if not self.is_local_prefix(s):
                continue

            if s not in subjects:
                self._logger.warning("%s has an AS.orderedItems predicate on the graph", s)
                subjects.add(s)
                problems += 1

        if fix and subjects:
            for collection in subjects:
                items = list(self.objects(subject=collection, predicate=AS.orderedItems))
                self._logger.info("Removing %s AS.orderedItems", collection)
                self.remove((collection, AS.orderedItems, None))
                self.set((collection, AS.totalItems, rdflib.Literal(0)))
                self._logger.info("Adding %d items of %s again", len(items), collection)
                for item in items:
                    self.add_to_collection(collection, item, deduplicate=False)
                problems -= 1
        self._logger.warning(
            "Collection schema has been fixed, but items order might be unexpected"
        )

        return problems

    @fsck_check
    def _fsck_totalitems(self, fix: bool = False) -> int:
        """AS.totalItems must provide actual item count"""
        problems = 0
        for collection in self.subjects(predicate=AS.totalItems):
            if not self.is_local_prefix(collection):
                continue

            type_ = self.value(subject=collection, predicate=RDF.type)
            if type_ == AS.OrderedCollection:
                actual_count = len(
                    list(
                        filter(
                            lambda t: t[2] != RDF.nil,
                            self.triples(
                                (collection, AS.items / (RDF.rest * "*") / RDF.first, None)
                            ),
                        )
                    )
                )
            else:
                actual_count = len(list(self.triples((collection, AS.items, None))))
            current_count = self.value(subject=collection, predicate=AS.totalItems).value

            if actual_count != current_count:
                self._logger.warning(
                    "Actual count %d of %s does not match current totalItems %d",
                    actual_count,
                    collection,
                    current_count,
                )
                problems += 1

                if fix:
                    self._logger.info("Setting AS.totalItems of %s to %d", collection, actual_count)
                    self.set((collection, AS.totalItems, rdflib.Literal(actual_count)))
                    problems -= 1

        return problems
