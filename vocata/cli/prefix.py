# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import typer

app = typer.Typer(help="Manage local prefixes (domains)")


@app.callback()
def select_prefix(
    ctx: typer.Context,
    prefix: str = typer.Argument(..., help="URI prefix to manage, e.g. https://example.com"),
):
    # FIXME allow specifying URL or just domain
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

    with ctx.obj["graph"] as graph:
        graph.set_local_prefix(ctx.obj["current_prefix"], is_local, reset_endpoints)


# FIXME rethink with a clear OIDC concept
@app.command()
def set_oauth_issuer(
    ctx: typer.Context,
    issuer: str = typer.Argument(..., help="Issuer URL of OAuth/OIDC issuer"),
    yes: bool = typer.Option(
        ...,
        help="Confirm action",
        prompt="Are you sure you want to change the issuer for the prefix?",
        confirmation_prompt=True,
    ),
):
    """Set OAuth/OIDC issuer for prefix"""
    if not yes:
        raise typer.Exit(code=1)

    with ctx.obj["graph"] as graph:
        if not graph.is_local_prefix(ctx.obj["current_prefix"]):
            raise typer.BadParameter(f"{ctx.obj['current_prefix']} is not a local prefix")

        graph.set_prefix_oauth_issuer(ctx.obj["current_prefix"], issuer)
