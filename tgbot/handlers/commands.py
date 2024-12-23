import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("start"))
async def user_start_handler(m: Message):
    await m.answer("Hello!")
