.. SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
   SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+

Instllation
===========

Prerequisites
-------------

Before installing Vocata, it is useful to meet a few prerequisites. For
the rest of this chapter, we will make the following assumptions:

-  Debian 12 (bookworm) host
-  NGINX reverse proxy
-  `certbot <https://certbot.eff.org/>`__ for certificate retrieval
-  ``vocata.example.com`` as the single local prefix to manage

Server / VM requirements
~~~~~~~~~~~~~~~~~~~~~~~~

-  1 GiB of RAM or more (depending on the instance size)
-  4 GiB of disk space or more (depending on the instance size)
-  Python 3.11 or newer (`Debian <https://www.debian.org/>`__ GNU/Linux
   12 (bookworm) recommended)

Auxiliary services
~~~~~~~~~~~~~~~~~~

-  `PostgreSQL <https://www.postgresql.org/>`__ 12 or newer recommended

   -  SQLite technically works, but is single-threaded

-  Reverse proxy for HTTPS (`NGINX <https://www.nginx.com/>`__
   recommended)

Network / domain / reachability requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  At least one domain name for a `local prefix <prefix.md>`__

   -  A/AAA records pointing to the Vocata server (IPv4 and IPv6
      dual-stack recommended)

-  SSL certificate for HTTPS (`Let’s
   Encrypt <https://letsencrypt.org/>`__ recommended)

Installation
------------

Using pip (from PyPI)
~~~~~~~~~~~~~~~~~~~~~

Vocata can be installed from the Python Package Index [PyPI]. It is
recommended to use a Python virtual environment for this setup.

.. code:: sh

   apt install python3-virtualenv
   mkdir /opt/vocata
   python3 -m virtualenv /opt/vocata/venv
   /opt/vocata/venv/bin/pip install "vocata[server,cli,postgresql]"  # or leave out postgresql

To start Vocata using `systemd <https://systemd.io/>`__, a service unit
like the following can be placed in
``/etc/systemd/system/vocata.service``:

.. code:: ini

   [Unit]
   Description=Vocata ActivityPub Server
   Documentation=https://docs.vocata.one
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   ExecStart=/opt/vocata/venv/bin/vocata

   [Install]
   WantedBy=multi-user.target

For the rest of the chapter, if the ``vocata`` or ``vocatactl`` commands
are used, remember to call it as ``/opt/vocata/venv/bin/vocata``.

Using docker-compose
~~~~~~~~~~~~~~~~~~~~

TBA

Setting up auxiliary services
-----------------------------

TBA

Basic/global configuration
--------------------------

The server can be configured using either a configuration file in
``/etc/vocata.toml`` (or several files in ``/etc/vocata.d/``), or using
environment variables.

In configuration files, use the `TOML <https://toml.io/en/>`__ syntax.
To use environment variables, translate the config keys into variable
names of the form ``VOC_group__subgroup__name`` (for a key
``group.subgroup.name``).

For an example configuration file, the default configuration, and the
documentation of the keys, see `the default_settings.toml
file <https://codeberg.org/Vocata/vocata/src/branch/main/vocata/default_settings.toml>`__
shipped with Vocata.
