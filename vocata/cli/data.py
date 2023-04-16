import json

import typer

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
