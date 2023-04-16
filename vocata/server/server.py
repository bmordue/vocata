import uvicorn

from ..settings import get_settings


def run_server():
    settings = get_settings()

    config = uvicorn.Config(
        "vocata.server.app:app", log_level=settings.log.level, **(settings.server.to_dict())
    )
    server = uvicorn.Server(config)
    server.run()
