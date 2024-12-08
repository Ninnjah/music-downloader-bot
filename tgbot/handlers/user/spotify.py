import logging

from aiogram import Router
from aiogram.types import Message

from celery.result import AsyncResult

from fluent.runtime import FluentLocalization

from broker.tasks.spotify_music import (
    download_album,
    download_artist,
    download_playlist,
    get_info, download_track,
)
from tgbot.filters.url import SpotifyUrlFilter, UrlList
from tgbot.services.tasks import generate_task_id

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(SpotifyUrlFilter())
async def spotify_url(m: Message, l10n: FluentLocalization, urls: UrlList):
    if urls.album:
        album = urls.album[0]
        album_info = get_info.delay(album.url).get()
        download_task: AsyncResult = download_album.apply_async(
            args=(m.from_user.id, album_info),
            task_id=generate_task_id(m.from_user.id),
        )

        await m.answer(
            l10n.format_value(
                "user-download-album",
                dict(
                    task_id=download_task.task_id,
                    artist=album_info[0]["album_artist"],
                    title=album_info[0]["album_name"],
                    track_count=album_info[0]["tracks_count"],
                ),
            )
        )

    elif urls.artist:
        artist = urls.artist[0]
        artist_info = get_info.delay(artist.url).get()
        download_task: AsyncResult = download_artist.apply_async(
            args=(m.from_user.id, artist_info),
            task_id=generate_task_id(m.from_user.id),
        )

        await m.answer(
            l10n.format_value(
                "user-download-artist",
                dict(
                    task_id=download_task.task_id,
                    artist=artist_info[0]["artist"],
                ),
            )
        )

    elif urls.playlist:
        playlist = urls.playlist[0]
        playlist_info = get_info.delay(playlist.url).get()
        download_task: AsyncResult = download_playlist.apply_async(
            args=(m.from_user.id, playlist_info),
            task_id=generate_task_id(m.from_user.id),
        )

        await m.answer(
            l10n.format_value(
                "user-download-playlist",
                dict(
                    task_id=download_task.task_id,
                    title=playlist_info[0]["list_name"],
                    track_count=playlist_info[0]["list_length"],
                ),
            )
        )

    elif urls.track:
        track = urls.track[0]
        track_info = get_info.delay(track.url).get()[0]
        download_task: AsyncResult = download_track.apply_async(
            args=(m.from_user.id, track_info),
            task_id=generate_task_id(m.from_user.id),
        )

        await m.answer(
            l10n.format_value(
                "user-download-track",
                dict(
                    task_id=download_task.task_id,
                    artist=track_info["artist"],
                    title=track_info["name"],
                ),
            )
        )
