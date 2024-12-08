import logging

from aiogram import Router
from aiogram.types import Message

from celery.result import AsyncResult

from fluent.runtime import FluentLocalization

from broker.tasks.yandex_music import (
    get_album_info, download_album,
    get_artist_info, download_artist,
    get_playlist_info, download_playlist,
    get_track_info, download_track,
)
from tgbot.filters.url import YandexUrlFilter, UrlList
from tgbot.services.tasks import generate_task_id

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(YandexUrlFilter())
async def yandex_url(m: Message, l10n: FluentLocalization, urls: UrlList):
    if urls.album:
        album = urls.album[0]
        album_info = get_album_info.delay(album.id).get()
        download_task: AsyncResult = download_album.apply_async(
            args=(m.from_user.id, album.id),
            task_id=generate_task_id(m.from_user.id),
        )
        await m.answer(
            l10n.format_value(
                "user-download-album",
                dict(
                    task_id=download_task.task_id,
                    artist=album_info["artists"][0]["name"],
                    title=album_info["title"],
                    track_count=album_info["track_count"],
                ),
            )
        )

    elif urls.artist:
        artist = urls.artist[0]
        artist_info = get_artist_info.delay(artist.id).get()
        download_task: AsyncResult = download_artist.apply_async(
            args=(m.from_user.id, artist.id),
            task_id=generate_task_id(m.from_user.id),
        )
        await m.answer(
            l10n.format_value(
                "user-download-artist",
                dict(
                    task_id=download_task.task_id,
                    artist=artist_info["name"],
                ),
            )
        )

    elif urls.playlist:
        playlist = urls.playlist[0]
        playlist_info = get_playlist_info.delay(playlist.owner, playlist.id).get()
        download_task: AsyncResult = download_playlist.apply_async(
            args=(m.from_user.id, playlist.owner, playlist.id),
            task_id=generate_task_id(m.from_user.id),
        )
        await m.answer(
            l10n.format_value(
                "user-download-playlist",
                dict(
                    task_id=download_task.task_id,
                    title=playlist_info["title"],
                    track_count=playlist_info["track_count"],
                ),
            )
        )

    elif urls.track:
        track = urls.track[0]
        track_info = get_track_info.delay(track.id).get()
        download_task: AsyncResult = download_track.apply_async(
            args=(m.from_user.id, track.id),
            task_id=generate_task_id(m.from_user.id),
        )
        await m.answer(
            l10n.format_value(
                "user-download-track",
                dict(
                    task_id=download_task.task_id,
                    artist=track_info["artists"][0]["name"],
                    title=track_info["title"],
                ),
            )
        )

    else:
        await m.answer("unsupported-url")
        return
