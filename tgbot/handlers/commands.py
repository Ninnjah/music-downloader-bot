import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from celery.result import AsyncResult

from broker.tasks.yandex_music import (
    get_album_info, download_album,
    get_artist_info, download_artist,
    get_playlist_info, download_playlist,
    get_track_info, download_track,
)
from tgbot.filters.yandex_url import YandexUrlFilter, UrlList

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(YandexUrlFilter())
async def url_download(m: Message, urls: UrlList):
    if urls.album:
        album = urls.album[0]
        album_info = get_album_info.delay(album.id).get()
        download_task: AsyncResult = download_album.delay(m.from_user.id, album.id)
        await m.answer("\n".join((album_info.get("title"), download_task.task_id)))

    elif urls.artist:
        artist = urls.artist[0]
        artist_info = get_artist_info.delay(artist.id).get()
        download_task: AsyncResult = download_artist.delay(m.from_user.id, artist.id)
        await m.answer("\n".join((artist_info.get("name"), download_task.task_id)))

    elif urls.playlist:
        playlist = urls.playlist[0]
        playlist_info = get_playlist_info.delay(playlist.owner, playlist.id).get()
        download_task: AsyncResult = download_playlist.delay(m.from_user.id, playlist.owner, playlist.id)
        await m.answer("\n".join((playlist_info.get("title"), download_task.task_id)))

    elif urls.track:
        track = urls.track[0]
        track_info = get_track_info.delay(track.id).get()
        download_task: AsyncResult = download_track.delay(m.from_user.id, track.id)
        await m.answer("\n".join((track_info.get("title"), download_task.task_id)))

    else:
        await m.answer("unsupported-url")
        return


@router.message(Command("start"))
async def user_start_handler(m: Message):
    await m.answer("Hello!")
