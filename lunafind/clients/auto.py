import re
from pathlib import Path
from typing import Union

from . import base
from .. import LOG


class NoClientFoundError(Exception):
    def __init__(self, premsg: str) -> None:
        super().__init__(
            f"{premsg} - Initialize a NetClient object, or add an appropriate "
            f"section in the lunafind config file."
        )


def get(value: Union[str, base.Client, None]) -> base.Client:
    from . import net

    if value is None:
        return net.DEFAULT

    if isinstance(value, base.Client):
        return value

    if isinstance(value, str) and value in net.ALIVE:
        return net.ALIVE[value]

    if isinstance(value, str):
        value = value.strip()


    if isinstance(value, str) and re.match(r"^\s*https?://.+", value):
        for name, client in net.ALIVE.items():
            site = client.site_url

            if value.startswith("http://") and site.startswith("https://"):
                value = value.replace("http://", "https://")

            if value.startswith(site):
                LOG.info("Auto-detect: using net client for %r.", name)
                return client

        raise NoClientFoundError(f"No appropriate client found for "
                                 f"URL {value!r}.")

    # In last resort, assume value is a path
    path = Path(value).expanduser()

    if not path.exists():
        raise FileNotFoundError("Path %r doesn't exist." % str(path))

    if path.is_file():
        path = path.parent

    if (path / "info.json").exists():
        path = path.parent

    LOG.info("Auto-detect: using local client for %s.",
             f"directory '{path!s}'" if path != Path(".") else "current dir")

    from . import local
    return local.Local(path)
