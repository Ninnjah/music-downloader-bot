import logging
import html

from aiogram import Router
from aiogram.types import Message

from fluent.runtime import FluentLocalization

from worker.tasks.yandex_music import (
    get_album_info, download_album,
    get_artist_info, download_artist,
    get_playlist_info, download_playlist,
    get_track_info, download_track,
)
from tgbot.filters.url import YandexUrlFilter, UrlList

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(YandexUrlFilter())
async def yandex_url(m: Message, l10n: FluentLocalization, urls: UrlList):
    if urls.album:
        album = urls.album[0]
        album_info = (await (await get_album_info.kiq(album.id)).wait_result()).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-album",
                dict(
                    artist=html.escape(album_info["artists"][0]["name"]),
                    title=html.escape(album_info["title"]),
                    track_count=album_info["track_count"],
                ),
            )
        )
        await download_album.kiq(
            user_id=m.from_user.id,
            album_id=album.id,
            reply_to_msg=msg.message_id,
        )

    elif urls.artist:
        artist = urls.artist[0]
        artist_info = (await (await get_artist_info.kiq(artist.id)).wait_result()).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-artist",
                dict(artist=html.escape(artist_info["name"])),
            )
        )
        await download_artist.kiq(
            user_id=m.from_user.id,
            artist_id=artist.id,
            reply_to_msg=msg.message_id,
        )

    elif urls.playlist:
        playlist = urls.playlist[0]
        playlist_info = (await (await get_playlist_info.kiq(playlist.owner, playlist.id)).wait_result()).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-playlist",
                dict(
                    title=html.escape(playlist_info["title"]),
                    track_count=playlist_info["track_count"],
                ),
            )
        )
        await download_playlist.kiq(
            user_id=m.from_user.id,
            owner_id=playlist.owner,
            playlist_id=playlist.id,
            reply_to_msg=msg.message_id,
        )

    elif urls.track:
        track = urls.track[0]
        track_info = (await (await get_track_info.kiq(track.id)).wait_result(timeout=5)).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-track",
                dict(
                    artist=html.escape(track_info["artists"][0]["name"]),
                    title=html.escape(track_info["title"]),
                ),
            )
        )
        await download_track.kiq(
            user_id=m.from_user.id,
            track_id=track.id,
            reply_to_msg=msg.message_id,
        )

    else:
        await m.answer("unsupported-url")
        return
