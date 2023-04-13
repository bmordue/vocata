import typer

from ..graph import get_graph

app = typer.Typer(help="Manage federation of activities and objects")


@app.command()
def push(
    ctx: typer.Context, activity_id: str = typer.Argument(..., help="ID (URL) of activity to push")
):
    """(Re-)push an activity with known ID"""
    graph = get_graph()

    succeeded, failed = graph.push(activity_id)

    if len(succeeded) > 0:
        ctx.obj["log"].info("Pushed activity %s to %d inboxes", activity_id, len(succeeded))
    if len(failed) > 0:
        ctx.obj["log"].warning("Failed to push activity %s to %d inboxes", activity_id, len(failed))


@app.command()
def pull(
    ctx: typer.Context,
    activity_id: str = typer.Argument(..., help="ID (URL) of activity/object to pull"),
):
    """(Re-)pull an activity or object with known ID"""
    graph = get_graph()

    success, _ = graph.pull(activity_id)
    if success:
        ctx.obj["log"].info("Pulled activity/object %s", activity_id)
    else:
        ctx.obj["log"].error("Failed to activity/object %s", activity_id)
