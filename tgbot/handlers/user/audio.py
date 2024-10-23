import logging
from io import BytesIO

from aiogram import Bot, Router
from aiogram.types import ContentType, Message
from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Button, Row, SwitchTo

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from tgbot.handlers.user.states.audio import AudioSG
from tgbot.services.l10n_dialog import L10NFormat

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def get_info(dialog_manager: DialogManager, **kwargs) -> dict:
    if dialog_manager.start_data and not dialog_manager.dialog_data:
        cover = dialog_manager.start_data.get("cover")
        if cover is not None:
            cover = MediaAttachment(ContentType.PHOTO, file_id=MediaId(cover))

        dialog_manager.dialog_data.update(
            artist=dialog_manager.start_data.get("artist") or 0,
            title=dialog_manager.start_data.get("title") or 0,
            album=dialog_manager.start_data.get("album") or 0,
            cover=cover,
        )

    else:
        cover = dialog_manager.dialog_data.get("cover")
        if cover is not None:
            cover = MediaAttachment(ContentType.PHOTO, file_id=MediaId(cover))

        dialog_manager.dialog_data.update(
            artist=dialog_manager.find("artist").get_value() or 0,
            title=dialog_manager.find("title").get_value() or 0,
            album=dialog_manager.find("album").get_value() or 0,
            cover=cover,
        )

    return dialog_manager.dialog_data


async def upload_audio(_, __, dialog_manager: DialogManager):
    ...


menu_dialog = Dialog(
    Window(
        DynamicMedia("cover"),
        L10NFormat("user-audio-preview"),
        SwitchTo(
            L10NFormat("user-audio-edit-artist"),
            id="to_artist",
            state=AudioSG.artist,
        ),
        SwitchTo(
            L10NFormat("user-audio-edit-title"),
            id="to_title",
            state=AudioSG.title,
        ),
        SwitchTo(
            L10NFormat("user-audio-edit-album"),
            id="to_album",
            state=AudioSG.album,
        ),
        SwitchTo(
            L10NFormat("user-audio-edit-cover"),
            id="to_cover",
            state=AudioSG.cover,
        ),
        Row(
            Cancel(L10NFormat("user-cancel")),
            Button(
                L10NFormat("user-audio-upload"),
                id="upload",
                on_click=upload_audio,
            )
        ),
        getter=get_info,
        state=AudioSG.preview,
    ),
)

router.include_routers(menu_dialog)
