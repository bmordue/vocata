import logging
from enum import StrEnum
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
import typer

from ..settings import get_settings
from . import actor
from . import data
from . import federation

LogLevel = StrEnum("LogLevel", {name: name for name in logging.getLevelNamesMapping().keys()})

app = typer.Typer()
app.add_typer(actor.app, name="actor")
app.add_typer(data.app, name="data")
app.add_typer(federation.app, name="federation")


@app.callback()
def configure_app(
    ctx: typer.Context,
    log_level: LogLevel = typer.Option(
        LogLevel.INFO, help="Log level for CLI output", case_sensitive=False
    ),
    config_file: Optional[Path] = typer.Option(None, help="Path to a TOML configuration file"),
    database: Optional[str] = typer.Option(None, help="URI of graph store database"),
):
    ctx.ensure_object(dict)

    overrides = {}
    overrides["log.level"] = log_level.value
    if config_file:
        overrides["settings_files"] = [config_file]
    if database:
        overrides["graph.database.uri"] = database
    ctx.obj["settings"] = get_settings(**overrides)

    logging.basicConfig(
        level=ctx.obj["settings"].log.level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    ctx.obj["log"] = logging.getLogger("vocata-cli")
