import logging
import html

from aiogram import Router
from aiogram.types import Message

from fluent.runtime import FluentLocalization

from worker.tasks.spotify_music import (
    download_album,
    download_artist,
    download_playlist,
    get_info, download_track,
)
from tgbot.filters.url import SpotifyUrlFilter, UrlList

logger = logging.getLogger(__name__)
router = Router(name=__name__)
TASK_TIMEOUT = 60


@router.message(SpotifyUrlFilter())
async def spotify_url(m: Message, l10n: FluentLocalization, urls: UrlList):
    if urls.album:
        album = urls.album[0]
        album_info = (await (await get_info.kiq(album.url)).wait_result(timeout=TASK_TIMEOUT)).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-album",
                dict(
                    artist=html.escape(album_info[0]["album_artist"]),
                    title=html.escape(album_info[0]["album_name"]),
                    track_count=album_info[0]["tracks_count"],
                ),
            )
        )
        await download_album.kiq(
            user_id=m.from_user.id,
            album=album_info[:5],
            reply_to_msg=msg.message_id,
        )

    elif urls.artist:
        artist = urls.artist[0]
        artist_info = (await (await get_info.kiq(artist.url)).wait_result(timeout=TASK_TIMEOUT)).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-artist",
                dict(artist=html.escape(artist_info[0]["artist"])),
            )
        )
        await download_artist.kiq(
            user_id=m.from_user.id,
            artist=artist_info[:5],
            reply_to_msg=msg.message_id,
        )

    elif urls.playlist:
        playlist = urls.playlist[0]
        playlist_info = (await (await get_info.kiq(playlist.url)).wait_result(timeout=TASK_TIMEOUT)).return_value

        msg = await m.answer(
            l10n.format_value(
                "user-download-playlist",
                dict(
                    title=html.escape(playlist_info[0]["list_name"]),
                    track_count=playlist_info[0]["list_length"],
                ),
            )
        )
        await download_playlist.kiq(
            user_id=m.from_user.id,
            playlist=playlist_info[:5],
            reply_to_msg=msg.message_id,
        )

    elif urls.track:
        track = urls.track[0]
        track_info = (await (await get_info.kiq(track.url)).wait_result(timeout=TASK_TIMEOUT)).return_value[0]

        msg = await m.answer(
            l10n.format_value(
                "user-download-track",
                dict(
                    artist=html.escape(track_info["artist"]),
                    title=html.escape(track_info["name"]),
                ),
            )
        )
        await download_track.kiq(
            user_id=m.from_user.id,
            song=track_info,
            reply_to_msg=msg.message_id,
        )
