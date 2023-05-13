.. SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
   SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+

The social graph
================

The network that is colloquially called the
`Fediverse <https://fediverse.party/>`__, or more precisely, the network
of servers using the `ActivityPub <https://activitypub.rocks/>`__
protocol, builds on a very well-established foundation.

ActivityStreams: The social graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The content on the `Fediverse <https://fediverse.party/>`__, technically
defined by the
`ActivityStreams <https://www.w3.org/TR/activitystreams-core/>`__
vocabulary, comprises the *social graph*.

This social graph is, from an information science perspective, a
*directed graph*, consisting of *triple statements* describing the
relations between its *nodes*. The concept, as well as the technical
implementation employed by `ActivityPub <https://activitypub.rocks/>`__,
is anything but new: it is the well-known
`RDF <https://www.w3.org/RDF/>`__ (*Resource Description Framework*)
graph model, which is also the foundation of some established standards
and tools on the web:

-  **RSS** and **Atom** for blog and podcast feeds
-  **OpenGraph** meta-data for websites
-  Ontological databases like **WikiData**
-  …and many more…

In `ActivityStreams <https://www.w3.org/TR/activitystreams-core/>`__,
this graph structure is used to model relationships between **Actors**
(users, groups, anyone who does something), **Activities** (create,
update, delete, follow,…) and **Objects** (notes, attachments,
events,…), all of which have unique *IRIs* (web addresses, colloquially
speaking).

If we got hold of all information from all instances on the
`Fediverse <https://fediverse.party/>`__ at once, it could be put
together in one big, consistend graph.

ActivityPub: Sub-graphs and federation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the name suggests, the `Fediverse <https://fediverse.party/>`__ is a
**federated** system, which means that it is comprised of several
instances that handle parts of it.

Relating this to the concept of the social graph, the implication is
that every instance handles a *sub-graph* of the global social graph.

The role of `ActivityPub <https://activitypub.rocks/>`__ is to ensure
that the sub-graph an insatance sees includes all nodes that are
relevant for the *actors* on the instance. For that purpose, objects
(actors and activities) can be **pulled** from other instances (using an
*HTTP GET request* to the URI of the desired node), and **pushed**
(using an *HTTP POST request* to a special node (an *inbox*) on another
instance).

In every pull and push, an even smaller sub-graph is transferred between
instances, containing exactly the nodes and statements relevant to merge
the desired object with the other instance’s sub-graph (technically,
what is transferred is the `CBD <https://www.w3.org/Submission/CBD/>`__
(*Concise Bounded Description*) of the object).

To conclude, `ActivityPub <https://activitypub.rocks/>`__ servers keep
pushing and pulling sub-graphs, so-called *Concise Bounded
Descriptions*, of objects that are relevant for their users.
