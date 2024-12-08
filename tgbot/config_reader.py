from dataclasses import dataclass
from os import path
from pathlib import Path
from sys import argv
from typing import List, Optional, Union

import yaml
from adaptix import Retort

retort = Retort()
if len(argv) > 1 and path.exists(argv[1]):
    config_path = argv[1]
else:
    config_path = "config.yaml"


@dataclass(frozen=True)
class Redis:
    enabled: bool
    prefix: str
    host: str = "localhost"
    port: int = 6379
    db: Union[str, int] = 0
    password: Optional[str] = None


@dataclass(frozen=True)
class Webhook:
    enabled: bool
    url: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None


@dataclass(frozen=True)
class Yandex:
    token: str


@dataclass(frozen=True)
class Spotify:
    id: str
    secret: str
    proxy: Optional[str] = None


@dataclass(frozen=True)
class Music:
    download_path: Path = Path("music")
    playlist_path: Path = Path("music")
    replace_playlist_path: bool = False


@dataclass(frozen=True)
class Subsonic:
    username: str
    password: str
    salt: str


@dataclass(frozen=True)
class Server:
    subsonic: Subsonic
    host: str = "localhost"
    port: int = 8080
    testing: bool = False


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_list: List[int]
    redis: Redis
    webhook: Webhook
    download_path: Path
    yandex: Yandex
    spotify: Spotify
    music: Music
    server: Server


with open(config_path, "r") as f:
    raw_config = yaml.safe_load(f.read())
    config = retort.load(raw_config, Config)
