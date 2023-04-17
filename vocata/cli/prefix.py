import typer

from ..graph import get_graph

app = typer.Typer(help="Manage local prefixes (domains)")


@app.callback()
def select_prefix(
    ctx: typer.Context,
    prefix: str = typer.Argument(..., help="URI prefix to manage, e.g. https://example.com"),
):
    ctx.obj["current_prefix"] = prefix


@app.command()
def set_local(
    ctx: typer.Context,
    is_local: bool = typer.Option(True, help="Is prefix local or not"),
    reset_endpoints: bool = typer.Option(True, help="Reset endpoint URLs for prefix to defaults"),
    yes: bool = typer.Option(
        ...,
        help="Confirm action",
        prompt="Are you sure you want to change the state of the prefix?",
        confirmation_prompt=True,
    ),
):
    """Set whether a URI prefix is local or not"""
    if not yes:
        raise typer.Exit(code=1)

    graph = get_graph(ctx.obj["settings"])

    graph.set_local_prefix(ctx.obj["current_prefix"], is_local, reset_endpoints)
