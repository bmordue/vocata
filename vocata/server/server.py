# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import uvicorn

from ..settings import get_settings


def run_server():
    settings = get_settings()

    config = uvicorn.Config(
        "vocata.server.app:app",
        log_level=settings.log.level,
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers,
    )
    server = uvicorn.Server(config)
    server.run()
