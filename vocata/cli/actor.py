# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from enum import StrEnum
from typing import Optional

import typer


class ActorType(StrEnum):
    application = "Application"
    group = "Group"
    organization = "Organization"
    person = "Person"
    service = "Service"


app = typer.Typer(help="Manage ActivityPub actors")


def render_account(account: str) -> str:
    # FIXME allow specifying account handle or URI
    if not account.startswith("acct:"):
        account = f"acct:{account}"
    return account


@app.command()
def create(
    ctx: typer.Context,
    account: str = typer.Argument(..., help="Account name of new actor, in user@domain.tld format"),
    name: Optional[str] = typer.Option(None, help="Display name of new actor"),
    actor_type: ActorType = typer.Option(ActorType.person, help="Actor type of new actor"),
    force: bool = typer.Option(
        False, help="Force creation even if prefix is not local (DANGEROUS!)"
    ),
):
    """Create a new local actor"""
    # FIXME support auto-assigned ID
    account = render_account(account)

    with ctx.obj["graph"] as graph:
        # FIXME allow specifying account handle or URI
        if not graph.is_valid_acct(account):
            ctx.obj["log"].error("The account name %s is invalid", account)
            raise typer.Exit(code=1)

        if graph.get_canonical_uri(account):
            ctx.obj["log"].error("The account %s already exists", account)
            raise typer.Exit(code=1)

        uri = graph.create_actor_from_acct(account, name or account, actor_type.value, force)

    if not uri:
        raise typer.Exit(code=2)


@app.command()
def set_password(
    ctx: typer.Context,
    account: str = typer.Argument(..., help="Account name of actor, in user@domain.tld format"),
    password: str = typer.Option(
        ..., help="Login password for C2S", prompt=True, confirmation_prompt=True, hide_input=True
    ),
):
    """Set C2S login password for an actor"""
    account = render_account(account)

    with ctx.obj["graph"] as graph:
        actor_uri = graph.get_canonical_uri(account)
        if actor_uri is None:
            ctx.obj["log"].error("The account %s does not exist", account)
            raise typer.Exit(code=1)

        graph.set_actor_password(actor_uri, password)
