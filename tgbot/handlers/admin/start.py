from aiogram import Router
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Column, Start

from tgbot.filters.dialog import IsSudoFilter
from tgbot.handlers.admin.states.admins import AdminSG
from tgbot.handlers.admin.states.broadcast import BroadcastSG
from tgbot.handlers.admin.states.localisation import LocaleSG
from tgbot.handlers.admin.states.menu import AdminMenuSG
from tgbot.handlers.admin.states.users import UserSG
from tgbot.services.l10n_dialog import L10NFormat

router = Router(name=__name__)


admin_menu_dialog = Dialog(
    Window(
        L10NFormat("admin-start-text"),
        Column(
            Start(
                L10NFormat("admin-button-list-admins"),
                id="admin_lst",
                state=AdminSG.lst,
                when=IsSudoFilter(),
            ),
            Start(
                L10NFormat("admin-button-list-users"),
                id="user_lst",
                state=UserSG.lst,
            ),
            Start(
                L10NFormat("admin-button-broadcast"),
                id="broadcast",
                state=BroadcastSG.main,
            ),
            Start(
                L10NFormat("admin-button-locale"),
                id="locale",
                state=LocaleSG.main,
            ),
        ),
        Cancel(L10NFormat("admin-button-close")),
        state=AdminMenuSG.main,
    ),
)


router.include_routers(admin_menu_dialog)
