.. SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
   SPDX-License-Identifier: LGPL-3.0-or-later OR CC-BY-SA-4.0+

Architecture of a Vocata instance
=================================

The server is a Python ASGI application built on top of
`Starlette <https://www.starlette.io/>`__, using
`Uvicorn <https://www.uvicorn.org/>`__ as ASGI server. For storing the
graph, it can use any SQL database supported by
`SQLAlchemy <https://www.sqlalchemy.org/>`__ (PostgreSQL and SQLite, but
also MySQL/MariaDB and some equally irrelevant databases).

Vocata in relation to the Fediverse
-----------------------------------

TBA

.. uml:: c4_context.puml


High-level overview of a Vocata instance setup
----------------------------------------------

TBA

.. uml:: c4_container.puml


Low-level components working in the Vocata server
--------------------------------------------------

TBA

.. uml:: c4_component.puml
