.. SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
   SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+

Basic design
============

The social graph in Vocata
--------------------------

Assuming the `graph structure <../introduction/graph.md>`__ of the
`Fediverse <https://fediverse.party/>`__, Vocata uses
`rdflib <https://rdflib.readthedocs.io/en/stable/>`__ to store its
sub-graph. In contrast to other
`ActivityPub <https://activitypub.rocks/>`__ servers, it does not derive
its own data structures from the objects it handles, but plainly
processes the graph operations defined by the protocol to traverse and
transform its sub-graph of the Fediverse.

Notable differences from other ActivityPub servers
--------------------------------------------------

Multi-domain / virtual hosting capability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vocata can handle as many domains (URI `prefixes <prefixes.md>`__) as
you want, by simply making it reachable over HTTPS under the desired
name (and flipping a safety seitch).

This results mostly from Vocata’s agnostic data structure – it simply
handles a `subgraph <../introduction/graph.md>`__ of the Fediverse,
without any need to care about who authoritatively manages any part of
it (if this sounds dangerous, read more in the `security
considerations <security.md>`__).
