from pathlib import Path
from typing import List, Optional, Union

from environ import bool_var, config, group, to_config, var


def admin_loader(value):
    return list(map(int, value.split(",")))


@config(prefix="REDIS_")
class Redis:
    enabled: bool = bool_var()
    prefix: str = var()
    host: str = var(default="localhost")
    port: int = var(default=6379)
    db: Union[str, int] = var(default=0)
    password: Optional[str] = var(default=None)


@config(prefix="WEBHOOK_")
class Webhook:
    enabled: bool = bool_var()
    url: Optional[str] = var(default=None)
    path: Optional[str] = var(default=None)
    port: Optional[int] = var(default=None)


@config(prefix="YANDEX_")
class Yandex:
    token: str = var()


@config(prefix="SPOTIFY_")
class Spotify:
    id: str = var()
    secret: str = var()
    proxy: Optional[str] = var(default=None)


@config(prefix="SUBSONIC_")
class Subsonic:
    username: str = var()
    password: str = var()
    salt: str = var()


@config(prefix="")
class Config:
    bot_token: str = var()
    admin_list: List[int] = var(converter=admin_loader)
    music_path: Path = var(default="/app/music", converter=Path)

    redis: Redis = group(Redis)
    webhook: Webhook = group(Webhook)
    yandex: Yandex = group(Yandex)
    spotify: Spotify = group(Spotify)
    subsonic: Subsonic = group(Subsonic)


def get_config() -> Config:
    return to_config(Config)


config = get_config()
