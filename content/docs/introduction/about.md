+++
title = "About Vocata and the Fediverse"
description = "Introduction on Vocata and its design philosophy"
weight = 10
sort_by = "weight"
template = "docs/page.html"

[extra]
toc = true
top = false
+++

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


[ActivityPub]: https://activitypub.rocks/
[Fediverse]: https://fediverse.party/
[Matrix]: https://matrix.org/
[Mastodon]: https://joinmastodon.org/
[Pixelfed]: https://pixelfed.org/
[PeerTUbe]: https://joinpeertube.org/
