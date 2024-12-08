import logging
from hashlib import md5
from dataclasses import dataclass
from typing import Any, Optional, Literal

import uvicorn

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from httpx import AsyncClient

from fluent.runtime import FluentLocalization

from litestar import Litestar, post, Response
from litestar.di import Provide
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from yandex_music import Album, Artist, Client, Track, Playlist

from tgbot.config_reader import config as global_config
from tgbot.fluent_loader import get_fluent_localization

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

config = global_config.server
SUBSONIC_DATA = {
    "u": config.subsonic.username,
    "t": md5((config.subsonic.password + config.subsonic.salt).encode("ASCII")).hexdigest(),
    "s": config.subsonic.salt,
    "v": "1.8.0",
    "c": "MusicDownloader",
    "f": "json",
}
SUBSONIC_URL = "https://music.nnjh.ru/rest/startScan"


async def get_bot() -> Bot:
    return Bot(
        token=global_config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )


async def get_client() -> Client:
    return Client(global_config.yandex.token)


async def get_l10n() -> FluentLocalization:
    return get_fluent_localization()


@dataclass
class Note:
    user_id: int
    task_id: str
    status: Literal["SUCCESS", "FAIL"]
    info: Optional[Any] = None


@post("/note_yandex", dependencies={"bot": Provide(get_bot), "client": Provide(get_client)})
async def task_note_yandex(data: Note, l10n: FluentLocalization, bot: Bot, client: Client) -> Response:
    raw_data = data.info

    if data.status == "FAIL":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value("note-fail", dict(task_id=data.task_id, info=data.info)),
        )
        return Response(status_code=200, content="Success")

    content_type = raw_data.pop("type")

    if content_type == "album":
        album = Album.de_json(raw_data, client)
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-album",
                dict(
                    task_id=data.task_id,
                    artist=album.artists_name()[0],
                    title=album.title,
                    track_count=album.track_count,
                )
            ),
        )

    elif content_type == "artist":
        artist = Artist.de_json(raw_data, client)
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-artist",
                dict(
                    task_id=data.task_id,
                    name=artist.name,
                ),
            ),
        )

    elif content_type == "playlist":
        playlist = Playlist.de_json(raw_data, client)
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-playlist",
                dict(
                    task_id=data.task_id,
                    title=playlist.title,
                    track_count=playlist.track_count,
                ),
            ),
        )

    elif content_type == "track":
        track = Track.de_json(raw_data, client)
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-track",
                dict(
                    task_id=data.task_id,
                    artist=track.artists_name()[0],
                    title=track.title,
                ),
            ),
        )

    else:
        return Response(status_code=400, content=f"Unsupported type {content_type}")

    async with AsyncClient() as client:
        await client.get(SUBSONIC_URL, params=SUBSONIC_DATA)
    return Response(status_code=200, content="Success")


@post("/note_spotify", dependencies={"bot": Provide(get_bot)})
async def task_note_spotify(data: Note, l10n: FluentLocalization, bot: Bot) -> Response:
    raw_data = data.info

    if data.status == "FAIL":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value("note-fail", dict(task_id=data.task_id, info=data.info)),
        )
        return Response(status_code=200, content="Success")

    content_type = raw_data.pop("type")

    if content_type == "album":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-album",
                dict(
                    task_id=data.task_id,
                    artist=raw_data["album_artist"],
                    title=raw_data["album_name"],
                    track_count=raw_data["tracks_count"],
                )
            ),
        )

    elif content_type == "artist":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-artist",
                dict(
                    task_id=data.task_id,
                    artist=raw_data["album_artist"],
                )
            ),
        )

    elif content_type == "playlist":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-playlist",
                dict(
                    task_id=data.task_id,
                    title=raw_data["list_name"],
                    track_count=raw_data["list_length"],
                ),
            ),
        )

    elif content_type == "track":
        await bot.send_message(
            chat_id=data.user_id,
            text=l10n.format_value(
                "note-track",
                dict(
                    task_id=data.task_id,
                    artist=raw_data["album_artist"],
                    title=raw_data["name"],
                )
            ),
        )

    else:
        return Response(status_code=400, content=f"Unsupported type {content_type}")

    async with AsyncClient() as client:
        await client.get(SUBSONIC_URL, params=SUBSONIC_DATA)
    return Response(status_code=200, content="Success")


backend_app = Litestar(
    route_handlers=[
        task_note_yandex,
        task_note_spotify
    ],
    debug=config.testing,
    dependencies={"l10n": get_l10n},
    openapi_config=OpenAPIConfig(
        title="Music Download Notification API",
        version="0.0.1",
        path="api",
        render_plugins=[ScalarRenderPlugin()],
    ),
    logging_config=LoggingConfig(
        log_exceptions="always",
    )
)

if __name__ == "__main__":
    uvicorn.run(
        "note_app:backend_app",
        host=config.host,
        port=config.port,
        reload=config.testing,
        log_level=logging.INFO,
        log_config=None,
    )
