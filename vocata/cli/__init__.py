import logging

from rich.logging import RichHandler
import typer

from . import actor
from . import federation

app = typer.Typer()
app.add_typer(actor.app, name="actor")
app.add_typer(federation.app, name="federation")


@app.callback()
def configure_app(ctx: typer.Context):
    ctx.ensure_object(dict)

    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    ctx.obj["log"] = logging.getLogger("vocata-cli")
