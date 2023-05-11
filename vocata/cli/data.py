# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import json
from IPython import start_ipython
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..graph import schema


app = typer.Typer(help="Manage ActivityPub data in graph")


@app.command()
def load_json(
    ctx: typer.Context,
    file: typer.FileBinaryRead = typer.Argument(..., help="JSON-LD file to load"),
    allow_non_local: bool = typer.Option(False, help="Allow adding objects outside local prefixes"),
):
    """Create a new local actor"""

    data = json.load(file)

    with ctx.obj["graph"] as graph:
        graph.add_jsonld(data, allow_non_local)


@app.command()
def dump_json(
    ctx: typer.Context,
    subject: str = typer.Argument(..., help="URI of subject to dump"),
    actor: Optional[str] = typer.Option(None, help="Dump with privileges of selected actor"),
):
    """Output a single subject as JSON-LD"""
    with ctx.obj["graph"] as graph:
        doc = graph.activitystreams_cbd(subject, actor).to_activitystreams(subject)

    print(json.dumps(doc, sort_keys=True, indent=2))


@app.command()
def subjects(
    ctx: typer.Context,
    prefix: Optional[str] = typer.Option(None, help="Limit subjects to selected URI prefix"),
):
    table = Table(title="Subject list")
    table.add_column("Subject", justify="left", no_wrap=True)
    table.add_column("Type", justify="left")

    with ctx.obj["graph"] as graph:
        for s, t in graph.uri_subjects(prefix):
            # FIXME better way to determine short type name
            table.add_row(s, t.fragment if t else "")

    console = Console()
    console.print(table)


@app.command()
def shell(ctx: typer.Context):
    """Run interactive Python shell with graph loaded"""

    user_ns = {}

    ctx.obj["log"].info("from vocata.graph.schema import %s", ", ".join(schema.__all__))
    for name in schema.__all__:
        user_ns[name] = getattr(schema, name)

    with ctx.obj["graph"] as graph:
        ctx.obj["log"].info("graph = ActivityPubGraph(...)")
        user_ns["graph"] = graph
        start_ipython(argv=[], user_ns=user_ns)
