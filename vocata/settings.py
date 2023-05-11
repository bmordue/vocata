# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from pathlib import Path
from dynaconf import Dynaconf
from dynaconf.base import LazySettings

_DEFAULTS_FILE = Path(__file__).parent / "default_settings.toml"


def get_settings(settings_files: str | list[str] = None, **overrides) -> LazySettings:
    if settings_files is None:
        settings_files = ["/etc/vocata.toml", "/etc/vocata.d/*.toml"]
    elif isinstance(settings_files, str):
        settings_files = [settings_files]

    settings = Dynaconf(
        envvar_prefix="VOC",
        core_loaders=["TOML"],
        preload=[_DEFAULTS_FILE],
        settings_files=settings_files,
        merge_enabled=True,
    )

    for name, value in overrides.items():
        settings.set(name, value)

    return settings
