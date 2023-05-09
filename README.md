# Vocata – Vocabulary-Agnostic Transport Agent

![Vocata logo](docs/static/vocata.svg)

## About Vocata and the Fediverse

Vocata is a *vocabulary-agnostic* [ActivityPub] server.
That means that, in contrast to other server software
on the [Fediverse], Vocata does not limit what types
of content can be handled by it, and how it is presented
to users.

As a *transport agent*, Vocata merely stores and forwards
content, and leaves any presentational decisions to a
client.

The principle of a transport agent is not new:

* In e-mail, an *MTA* (Mail transport Agent) is responsible
  for storing and forwarding e-mail, and users use a *MUA*
  (Mail User Agent, colloquially: an e-mail program, or
  webmail) to send and receive mail
* In [Matrix], a *homeserver* is responsible for handling
  the rooms and events of users, and users use any Matrix
  client to log in to their homeserver

### Benefits of separating client and server

The [Fediverse], at the time of writing, is build on *platforms*
that blend the [ActivityPub] protocol with an opinionated
presentational layer:

* [Mastodon] offers a micro-blogging platform
* [Pixelfed] offers a photo community platform
* [PeerTube] offers a video hosting and streaming platform
* …and many more…

All these platforms are, to some extent, *interoperable*,
because they all rely on the [ActivityPub] protocol. However,
they all have a baked-in concept, dictating how content is
presented to users, and this unification implies some
limitations:

* An identity on the [Fediverse] is inextricably linked with
  the platform. Identities (e.g. accounts) cannot be ported
  between platforms. So, if a user wants a microblog-style
  presentation **and** a gallery-style presentation, they
  are forced to use two identities.
* Client-server interoperability is very limited, because
  each platform implements its own client-server protocol,
  considering the presentational concept of the platform

By shifting the [Fediverse] towards a separation between
servers and clients, or *transport agents* and *user agents*
in e-mail terms, it can overcome these limitations.


### Conclusion: What is Vocata?

**Vocata** implements an [ActivityPub] server, and nothing
more. It offers an interface for clients to send and
receive content to and from the [Fediverse] with an
identity, and handles federation with other servers on
behalf of users.

With an account on a Vocata server, a user gains access
to the [Fediverse] with a chosen identity, and can then use
any client to act with that identity.


## Technical: What the Fediverse really is

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
insance sees includes all nodes that are relevant for the *actors*
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

## Implementation details of Vocata

Assuming the graph structure of the [Fediverse], Vocata
uses [rdflib] to store its sub-graph. In contrast to other
[ActivityPub] servers, it does not derive its own data
structures from the objects it handles, but plainly
processes the graph operations defined by the protocol
to traverse and transform its sub-graph of the Fediverse.

## Running the Vocata server

The server is a Python ASGI application built on top of
[Starlette], using [Uvicorn] as ASGI server. For storing
the graph, it can use any SQL database supported by
[SQLAlchemy].

### Installation

To install the server, you can either use the [Poetry]
tool also used for development, or install the `vocata`
Python package into your own environment:

```sh
# Install using poetry
git clone https://codeberg.org/Vocata/vocata
cd vocata
poetry install -E server -E cli
poetry run vocata

# Install using pip in your own environment
pip install "vocata[server,cli]"
vocata
```

The extras `server` and `cli` install the dependencies
for running the server and the `vocata` binary;
the `cli` extra installs the `vocatactl` control
utiliy.

### Configuration

The server can be configured using either a configuration
file in `/etc/vocata.toml` (or several files in `/etc/vocata.d/`,
or using environment variables.

In configuration files, use the [TOML] syntax. To use environment
variables, translate the config keys into variable names of the form
`VOC_group__subgroup__name` (for a key `group.subgroup.name`).

For an example configuration file, the default configuration, and
the documentation of the keys, see
[the default_settings.toml file](./vocata/default_settings.toml) shipped
with Vocata.

### Setting up a domain (prefix)

Domains are managed as URI prefixes in Vocata. As every object in
[ActivityPub] has a unique ID, which maps directly to an HTTP URL,
the server can determine the "domain" prefix by splitting the object
ID after the hostname.

In order to properly implement ActivityPub as a global social graph,
Vocata stores all known objects in its graph store, but it only allows
local management of objects under known local prefixes. That means
that in order to use a domain with Vocata, you need to declare it
a local prefix:

```shell
# Declare example.com a local prefix
vocatactl prefix https://example.com set-local
```

From this point on, Vocata feels responsible for the prefix, and
you can start using it by creating a local actor:

```shell
# Create actor test under the example.com domain,
# with display name "Test User"
vocatactl actor create test@example.com "Test User"
```

## The Vocata logo

Vocata's logo reflects many of the concepts and assumptions
established above:

* It is based on the triangles, the arrow, and the colors
  of the [ActivityPub] logo
* Two more colors from a derived palette have been added, to
  highlight that the Fediverse should be more colorful than
  some semi-interoperable, yet somewhat zoned platforms
* Three triangles form a [Sierpinski triangle], which is a
  fractal, much like the structure of the [ActivityPub] social
  graph (global graph, instance sub-graph, and CBD transferred
  between them being three of its iterations)


[ActivityPub]: https://activitypub.rocks/
[Fediverse]: https://fediverse.party/
[Matrix]: https://matrix.org/
[Mastodon]: https://joinmastodon.org/
[Pixelfed]: https://pixelfed.org/
[PeerTUbe]: https://joinpeertube.org/
[ActivityStreams]: https://www.w3.org/TR/activitystreams-core/
[RDF]: https://www.w3.org/RDF/
[CBD]: https://www.w3.org/Submission/CBD/
[rdflib]: https://rdflib.readthedocs.io/en/stable/
[Sierpinski triangle]: https://en.wikipedia.org/wiki/Sierpi%C5%84ski_triangle
[Starlette]: https://www.starlette.io/
[Uvicorn]: https://www.uvicorn.org/
[SQLAlchemy]: https://www.sqlalchemy.org/
[Poetry]: https://python-poetry.org/
[TOML]: https://toml.io/en/
