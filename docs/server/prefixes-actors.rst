.. SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
   SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+

Prefixes (local domains) and actors
===================================

How local prefixes work
-----------------------

Domains are managed as URI prefixes in Vocata. As every object in
`ActivityPub <https://activitypub.rocks/>`__ has a unique ID, which maps
directly to an HTTP URL, the server can determine the “domain” prefix by
splitting the object ID after the hostname.

In order to properly implement ActivityPub as a global social graph,
Vocata stores all known objects in its graph store, but it only allows
local management of objects under known local prefixes.

Setting up a local prefix (domain)
----------------------------------

In order to use a domain with Vocata, you need to declare it a local
prefix:

.. code:: sh

   # Declare vocata.example.com a local prefix
   vocatactl prefix https://vocata.example.com set-local

From this point on, Vocata feels responsible for the prefix, and you can
start using it.

.. code:: sh

   # Create actor test under the vocata.example.com domain,
   # with display name "Test User"
   vocatactl actor test@vocata.example.com create --name "Test User"
