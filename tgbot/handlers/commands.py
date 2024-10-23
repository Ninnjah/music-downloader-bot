from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from fluent.runtime import FluentLocalization

from tgbot.database import User
from tgbot.filters import IsAdminFilter
from tgbot.handlers.admin.states.menu import AdminMenuSG
from tgbot.services.repository import Repo

router = Router(name=__name__)


@router.message(Command("admin"), IsAdminFilter())
async def admin_handler(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("start"))
async def user_start_handler(m: Message, l10n: FluentLocalization, repo: Repo):
    await repo.add_user(
        user=User(
            id=m.from_user.id,
            firstname=m.from_user.first_name,
            lastname=m.from_user.last_name,
            username=m.from_user.username,
        )
    )
    await m.answer(l10n.format_value("user-start-text"))
