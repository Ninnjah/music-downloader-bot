from aiogram import F, Router
from aiogram.enums.chat_type import ChatType

from tgbot.filters import IsAdminFilter

from . import start, audio

__all__ = ("router",)

router = Router(name=__name__)
router.message.filter(IsAdminFilter(), F.chat.type.in_({ChatType.PRIVATE}))
router.callback_query.filter(IsAdminFilter(), F.message.chat.type.in_({ChatType.PRIVATE}))

router.include_routers(
    start.router,
    audio.router,
)
