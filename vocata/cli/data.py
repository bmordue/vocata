import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..graph import get_graph


app = typer.Typer(help="Manage ActivityPub data in graph")


@app.command()
def load_json(
    ctx: typer.Context,
    file: typer.FileBinaryRead = typer.Argument(..., help="JSON-LD file to load"),
    allow_non_local: bool = typer.Option(False, help="Allow adding objects outside local prefixes"),
):
    """Create a new local actor"""

    data = json.load(file)

    graph = get_graph(ctx.obj["settings"])
    graph.add_jsonld(data, allow_non_local)


@app.command()
def dump_json(
    ctx: typer.Context,
    subject: str = typer.Argument(..., help="URI of subject to dump"),
    actor: Optional[str] = typer.Option(None, help="Dump with privileges of selected actor"),
):
    """Output a single subject as JSON-LD"""
    graph = get_graph(ctx.obj["settings"])

    doc = graph.activitystreams_cbd(subject, actor).to_activitystreams(subject)

    print(json.dumps(doc, sort_keys=True, indent=2))


@app.command()
def subjects(
    ctx: typer.Context,
    prefix: Optional[str] = typer.Option(None, help="Limit subjects to selected URI prefix"),
):
    graph = get_graph(ctx.obj["settings"])

    table = Table(title="Subject list")
    table.add_column("Subject", justify="left", no_wrap=True)
    table.add_column("Type", justify="left")

    for s, t in graph.uri_subjects(prefix):
        # FIXME better way to determine short type name
        table.add_row(s, t.fragment if t else "")

    console = Console()
    console.print(table)
