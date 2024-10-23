from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from tgbot.handlers.user.states.menu import MenuSG

router = Router(name=__name__)


@router.message(Command("start"))
async def user_start_handler(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MenuSG.main, mode=StartMode.RESET_STACK)
