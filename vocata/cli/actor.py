from enum import StrEnum

import typer

from ..graph import get_graph


class ActorType(StrEnum):
    application = "Application"
    group = "Group"
    organization = "Organization"
    person = "Person"
    service = "Service"


app = typer.Typer(help="Manage ActivityPub actors")


@app.command()
def create(
    ctx: typer.Context,
    account: str = typer.Argument(..., help="Account name of new actor, in user@domain.tld format"),
    name: str = typer.Argument(..., help="Display name of new actor"),
    actor_type: ActorType = typer.Option(ActorType.person, help="Actor type of new actor"),
):
    """Create a new local actor"""
    graph = get_graph()

    if not graph.is_valid_acct(account):
        ctx.obj["log"].error("The account name %s is invalid", account)
        raise typer.Exit(code=1)

    if graph.get_actor_uri_by_acct(account):
        ctx.obj["log"].error("The account %s already exists", account)
        raise typer.Exit(code=1)

    uri = graph.create_actor_from_acct(account, name, actor_type.value)

    ctx.obj["log"].info("Account %s created at URI %s", account, str(uri))
