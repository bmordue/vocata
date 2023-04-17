from typing import Optional

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

    graph.set_local_prefix(ctx.obj["current_prefix"], is_local)


@app.command()
def set_endpoint(
    ctx: typer.Context,
    reset: bool = typer.Option(False, help="Reset endpoints for prefix (before setting new)"),
    oauth_authorization_endpoint: Optional[str] = typer.Option(
        None, help="OAuth 2.0 Authorization endpoint"
    ),
    oauth_token_endpoint: Optional[str] = typer.Option(None, help="OAuth 2.0 Token endpoint"),
    oauth_registration_endpoint: Optional[str] = typer.Option(
        None, help="OAuth 2.0 Client Registration endpoint"
    ),
    proxy_url: Optional[str] = typer.Option(None, help="Proxy for remote ActivityStreams"),
):
    """Configure external OAuth provider"""
    graph = get_graph(ctx.obj["settings"])

    if reset:
        graph.reset_prefix_endpoints(ctx.obj["current_prefix"])

    if oauth_authorization_endpoint is not None:
        graph.set_prefix_endpoint(
            ctx.obj["current_prefix"], "oauthAuthorizationEndpoint", oauth_authorization_endpoint
        )
    if oauth_token_endpoint is not None:
        graph.set_prefix_endpoint(
            ctx.obj["current_prefix"], "oauthTokenEndpoint", oauth_token_endpoint
        )
    if oauth_registration_endpoint is not None:
        graph.set_prefix_endpoint(
            ctx.obj["current_prefix"], "oauthRegistrationEndpoint", oauth_registration_endpoint
        )
    if proxy_url is not None:
        graph.set_prefix_endpoint(ctx.obj["current_prefix"], "proxyUrl", proxy_url)
