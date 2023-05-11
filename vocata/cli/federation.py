# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import typer

app = typer.Typer(help="Manage federation of activities and objects")


@app.command()
def push(
    ctx: typer.Context, activity_id: str = typer.Argument(..., help="ID (URL) of activity to push")
):
    """(Re-)push an activity with known ID"""
    with ctx.obj["graph"] as graph:
        succeeded, failed = graph.push(activity_id)

    if len(failed) > 0:
        raise typer.Exit(code=2)


@app.command()
def pull(
    ctx: typer.Context,
    activity_id: str = typer.Argument(..., help="ID (URL) of activity/object to pull"),
):
    """(Re-)pull an activity or object with known ID"""
    with ctx.obj["graph"] as graph:
        success, _ = graph.pull(activity_id)

    if not success:
        raise typer.Exit(code=2)
