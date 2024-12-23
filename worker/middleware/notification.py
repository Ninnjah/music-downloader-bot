import logging
import html
from hashlib import md5
from typing import Any, Coroutine, Union, Optional

from httpx import AsyncClient
from aiogram import Bot
from fluent.runtime import FluentLocalization
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult
from yandex_music import Album, Artist, Track, Playlist

from tgbot.config_reader import config

logger = logging.getLogger(__name__)


class YandexNoteMiddleware(TaskiqMiddleware):
    LABEL = "yandex"
    SUBSONIC_DATA = {
        "u": config.subsonic.username,
        "t": md5((config.subsonic.password + config.subsonic.salt).encode("ASCII")).hexdigest(),
        "s": config.subsonic.salt,
        "v": "1.8.0",
        "c": "MusicDownloader",
        "f": "json",
    }
    SUBSONIC_URL = "https://music.nnjh.ru/rest/startScan"

    async def post_execute(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
    ) -> "Union[None, Coroutine[Any, Any, None]]":
        if message.labels.get("note") != self.LABEL or result.is_err:
            return

        data = result.return_value
        bot: Bot = message.kwargs["bot"]
        l10n: FluentLocalization = message.kwargs["l10n"]
        user_id: int = message.kwargs["user_id"]
        task_id: str = message.task_id
        reply_to_msg: Optional[int] = message.kwargs.get("reply_to_msg")

        if isinstance(data, Album):
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-album",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data.artists_name()[0]),
                        title=html.escape(data.title),
                        track_count=data.track_count,
                    )
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif isinstance(data, Artist):
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-artist",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data.name),
                    ),
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif isinstance(data, Playlist):
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-playlist",
                    dict(
                        task_id=task_id,
                        title=html.escape(data.title),
                        track_count=data.track_count,
                    ),
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif isinstance(data, Track):
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-track",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data.artists_name()[0]),
                        title=html.escape(data.title),
                    ),
                ),
                reply_to_message_id=reply_to_msg,
            )

        else:
            return

        async with AsyncClient() as client:
            await client.get(self.SUBSONIC_URL, params=self.SUBSONIC_DATA)

        return

    async def on_error(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
        exception: BaseException,
    ) -> TaskiqMessage:
        if message.labels.get("note") != self.LABEL:
            return message

        bot: Bot = message.kwargs["bot"]
        l10n: FluentLocalization = message.kwargs["l10n"]
        chat_id: int = message.kwargs["user_id"]
        reply_to_msg: Optional[int] = message.kwargs.get("reply_to_msg")

        logger.warning(
            "task - %s[%s] - %s",
            message.task_id, message.task_name, exception
        )
        await bot.send_message(
            chat_id=chat_id,
            text=l10n.format_value(
                "note-fail",
                dict(task_id=message.task_id, info=repr(exception)),
            ),
            reply_to_message_id=reply_to_msg,
        )
        return message


class SpotifyNoteMiddleware(TaskiqMiddleware):
    LABEL = "spotify"
    SUBSONIC_DATA = {
        "u": config.subsonic.username,
        "t": md5((config.subsonic.password + config.subsonic.salt).encode("ASCII")).hexdigest(),
        "s": config.subsonic.salt,
        "v": "1.8.0",
        "c": "MusicDownloader",
        "f": "json",
    }
    SUBSONIC_URL = "https://music.nnjh.ru/rest/startScan"

    async def post_execute(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
    ) -> "Union[None, Coroutine[Any, Any, None]]":
        if message.labels.get("note") != self.LABEL or result.is_err:
            return result

        data = result.return_value
        bot: Bot = message.kwargs["bot"]
        l10n: FluentLocalization = message.kwargs["l10n"]
        user_id: int = message.kwargs["user_id"]
        task_id: str = message.task_id.split(":")[-1]
        reply_to_msg: Optional[int] = message.kwargs.get("reply_to_msg")

        content_type = data.pop("type")

        if content_type == "album":
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-album",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data["album_artist"]),
                        title=html.escape(data["album_name"]),
                        track_count=data["tracks_count"],
                    )
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif content_type == "artist":
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-artist",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data["album_artist"]),
                    )
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif content_type == "playlist":
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-playlist",
                    dict(
                        task_id=task_id,
                        title=html.escape(data["list_name"]),
                        track_count=data["list_length"],
                    ),
                ),
                reply_to_message_id=reply_to_msg,
            )

        elif content_type == "track":
            await bot.send_message(
                chat_id=user_id,
                text=l10n.format_value(
                    "note-track",
                    dict(
                        task_id=task_id,
                        artist=html.escape(data["album_artist"]),
                        title=html.escape(data["name"]),
                    )
                ),
                reply_to_message_id=reply_to_msg,
            )

        else:
            return

        async with AsyncClient() as client:
            await client.get(self.SUBSONIC_URL, params=self.SUBSONIC_DATA)

        return

    async def on_error(
        self,
        message: "TaskiqMessage",
        result: "TaskiqResult[Any]",
        exception: BaseException,
    ) -> TaskiqMessage:
        if message.labels.get("note") != self.LABEL:
            return message
        bot: Bot = message.kwargs["bot"]
        l10n: FluentLocalization = message.kwargs["l10n"]
        chat_id: int = message.kwargs["user_id"]
        task_id: str = message.task_id.split(":")[-1]
        reply_to_msg: Optional[int] = message.kwargs.get("reply_to_msg")

        logger.warning(
            "task - %s[%s] - %s",
            message.task_id, message.task_name, exception
        )
        await bot.send_message(
            chat_id=chat_id,
            text=l10n.format_value(
                "note-fail",
                dict(task_id=task_id, info=repr(exception)),
            ),
            reply_to_message_id=reply_to_msg,
        )
        return message
