<!--
SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>

SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+
-->

+++
title = "The social graph"
description = "An opinionated and objective introduction to what the Fediverse actually is"
weight = 20
sort_by = "weight"
template = "docs/page.html"

[extra]
toc = true
top = false
+++

The network that is colloquially called the [Fediverse], or
more precisely, the network of servers using the [ActivityPub]
protocol, builds on a very well-established foundation.

### ActivityStreams: The social graph

The content on the [Fediverse], technically defined by the
[ActivityStreams] vocabulary, comprises the *social graph*.

This social graph is, from an information science perspective,
a *directed graph*, consisting of *triple statements* describing
the relations between its *nodes*. The concept, as well as the
technical implementation employed by [ActivityPub], is anything
but new: it is the well-known [RDF] (*Resource Description Framework*)
graph model, which is also the foundation of some established
standards and tools on the web:

* **RSS** and **Atom** for blog and podcast feeds
* **OpenGraph** meta-data for websites
* Ontological databases like **WikiData**
* …and many more…

In [ActivityStreams], this graph structure is used to model
relationships between **Actors** (users, groups, anyone who does
something), **Activities** (create, update, delete, follow,…) and **Objects**
(notes, attachments, events,…), all of which have unique *IRIs*
(web addresses, colloquially speaking).

If we got hold of all information from all instances on the
[Fediverse] at once, it could be put together in one big, consistend
graph.

### ActivityPub: Sub-graphs and federation

As the name suggests, the [Fediverse] is a **federated** system,
which means that it is comprised of several instances that handle
parts of it.

Relating this to the concept of the social graph, the implication
is that every instance handles a *sub-graph* of the global social
graph.

The role of [ActivityPub] is to ensure that the sub-graph an
insatance sees includes all nodes that are relevant for the *actors*
on the instance. For that purpose, objects (actors and activities)
can be **pulled** from other instances (using an *HTTP GET request*
to the URI of the desired node), and **pushed** (using an
*HTTP POST request* to a special node (an *inbox*) on another
instance).

In every pull and push, an even smaller sub-graph is transferred
between instances, containing exactly the nodes and statements
relevant to merge the desired object with the other instance's
sub-graph (technically, what is transferred is the [CBD]
(*Concise Bounded Description*) of the object).

To conclude, [ActivityPub] servers keep pushing and pulling
sub-graphs, so-called *Concise Bounded Descriptions*, of objects
that are relevant for their users.

[ActivityPub]: https://activitypub.rocks/
[Fediverse]: https://fediverse.party/
[ActivityStreams]: https://www.w3.org/TR/activitystreams-core/
[RDF]: https://www.w3.org/RDF/
[CBD]: https://www.w3.org/Submission/CBD/
