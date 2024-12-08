import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from celery.result import AsyncResult

from fluent.runtime import FluentLocalization

from broker.tasks.yandex_music import (
    get_album_info, download_album,
    get_artist_info, download_artist,
    get_playlist_info, download_playlist,
    get_track_info, download_track,
)
from tgbot.filters.url import SpotifyUrlFilter, YandexUrlFilter, UrlList
from tgbot.services.tasks import generate_task_id

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("start"))
async def user_start_handler(m: Message):
    await m.answer("Hello!")
