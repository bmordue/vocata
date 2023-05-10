<!--
SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>

SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+
-->

+++
title = "Prefixes (local domains) and actors"
description = "Managing prefixes (domains) Vocata is responsible for"
weight = 30
sort_by = "weight"
template = "docs/page.html"

[extra]
toc = true
top = false
+++

## How local prefixes work

Domains are managed as URI prefixes in Vocata. As every object in
[ActivityPub] has a unique ID, which maps directly to an HTTP URL,
the server can determine the "domain" prefix by splitting the object
ID after the hostname.

In order to properly implement ActivityPub as a global social graph,
Vocata stores all known objects in its graph store, but it only allows
local management of objects under known local prefixes.

## Setting up a local prefix (domain)

In order to use a domain with Vocata, you need to declare it
a local prefix:

```sh
# Declare vocata.example.com a local prefix
vocatactl prefix https://vocata.example.com set-local
```

From this point on, Vocata feels responsible for the prefix, and
you can start using it.

```sh
# Create actor test under the vocata.example.com domain,
# with display name "Test User"
vocatactl actor create test@vocata.example.com "Test User"
```

[ActivityPub]: https://activitypub.rocks/
