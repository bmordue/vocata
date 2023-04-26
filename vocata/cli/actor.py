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


@app.callback()
def select_account(
    ctx: typer.Context,
    account: str = typer.Argument(..., help="Account name of new actor, in user@domain.tld format"),
):
    # FIXME allow specifying account handle or URI
    ctx.obj["current_account"] = account


@app.command()
def create(
    ctx: typer.Context,
    name: Optional[str] = typer.Option(None, help="Display name of new actor"),
    actor_type: ActorType = typer.Option(ActorType.person, help="Actor type of new actor"),
    force: bool = typer.Option(
        False, help="Force creation even if prefix is not local (DANGEROUS!)"
    ),
):
    """Create a new local actor"""
    # FIXME support auto-assigned ID
    account = ctx.obj["current_account"]

    with ctx.obj["graph"] as graph:
        # FIXME allow specifying account handle or URI
        if not graph.is_valid_acct(account):
            ctx.obj["log"].error("The account name %s is invalid", account)
            raise typer.Exit(code=1)

        if graph.get_actor_uri_by_acct(account):
            ctx.obj["log"].error("The account %s already exists", account)
            raise typer.Exit(code=1)

        uri = graph.create_actor_from_acct(account, name or account, actor_type.value, force)

    if not uri:
        raise typer.Exit(code=2)


@app.command()
def set_password(
    ctx: typer.Context,
    password: str = typer.Option(
        ..., help="Login password for C2S", prompt=True, confirmation_prompt=True, hide_input=True
    ),
):
    """Set C2S loing password for an actor"""
    account = ctx.obj["current_account"]

    with ctx.obj["graph"] as graph:
        actor_uri = graph.get_actor_uri_by_acct(account)
        if actor_uri is None:
            ctx.obj["log"].error("The account %s does not exist", account)
            raise typer.Exit(code=1)

        graph.set_actor_password(actor_uri, password)
