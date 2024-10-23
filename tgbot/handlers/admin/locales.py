from pathlib import Path
from typing import Iterable, Union

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column

from tgbot.fluent_loader import ReloadableFluentLocalization
from tgbot.handlers.admin.states.localisation import LocaleSG
from tgbot.services.l10n_dialog import L10NFormat

router = Router(name=__name__)
EDITED_PATH = Path("locales", "ru", "edit_locales.ftl")


async def get_edited(dialog_manager: DialogManager, **kwargs):
    return {"edited": EDITED_PATH.exists()}


async def download_origin(callback_query: CallbackQuery, _: Button, dialog_manager: DialogManager):
    def load_locales(path_list: Union[Iterable[Path], Path]) -> str:
        text = ""
        for path in path_list:
            if path.is_file() and path.suffix == ".ftl":
                text += f"{path.name.center(64, '#')}\n{path.read_text()}\n\n"
            elif path.is_dir():
                text += load_locales(path.iterdir())

        return text

    allowed_paths = (
        Path("locales", "ru", "commands.ftl"),
        Path("locales", "ru", "user"),
        Path("locales", "ru", "admin"),
    )

    edit_text = load_locales(allowed_paths)

    file = BufferedInputFile(edit_text.encode("utf-8"), filename="edit_locales.ftl")
    await callback_query.message.answer_document(file)


async def download_current(callback_query: CallbackQuery, _: Button, dialog_manager: DialogManager):
    with EDITED_PATH.open("rb") as f:
        file = BufferedInputFile(f.read(), filename="edit_locales.ftl")

    await callback_query.message.answer_document(file)


async def update_handler(m: Message, _: MessageInput, dialog_manager: DialogManager):
    l10n: ReloadableFluentLocalization = dialog_manager.middleware_data["l10n"]
    await m.bot.download(m.document.file_id, EDITED_PATH)
    l10n.reload()

    await m.reply(l10n.format_value("admin-locale-uploaded"))


locale_dialog = Dialog(
    Window(
        L10NFormat("admin-locale"),
        Column(
            Button(
                L10NFormat("admin-button-locale-origin"),
                id="origin_download",
                on_click=download_origin,
            ),
            Button(
                L10NFormat("admin-button-locale-current"),
                id="current_download",
                on_click=download_current,
                when=F["edited"],
            ),
        ),
        MessageInput(
            func=update_handler,
            content_types=[ContentType.DOCUMENT],
        ),
        Cancel(L10NFormat("admin-button-back")),
        state=LocaleSG.main,
        getter=get_edited,
    ),
)


router.include_routers(locale_dialog)
