import logging
from io import BytesIO

from aiogram import Bot, Router
from aiogram.types import ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Column, Start

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

from tgbot.config_reader import config
from tgbot.handlers.user.states.menu import MenuSG
from tgbot.services.l10n_dialog import L10NFormat
from tgbot.models.album import Album

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def process_query(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    logger.info("Hello!")


async def process_audio(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    album: Album = dialog_manager.middleware_data["album"]
    bot: Bot = dialog_manager.middleware_data["bot"]

    for audio in album.audio:
        with BytesIO() as f:
            file_data = await bot.get_file(audio.file_id)
            await bot.download_file(file_data.file_path, destination=f)
            audio_bytes = f.read()
            f.seek(0)

            tags = MP3(f)
            artist_path = config.download_path / tags.get("TPE1").text[0].split(",")[0]
            artist_path.mkdir(parents=True, exist_ok=True)
            artist_path /= (tags.get("TIT2").text[0] + ".mp3")
            with artist_path.open("wb") as audio_file:
                audio_file.write(audio_bytes)
            tags.save(artist_path)


menu_dialog = Dialog(
    Window(
        L10NFormat("user-start-text"),
        MessageInput(
            func=process_query,
            content_types=[ContentType.TEXT],
        ),
        MessageInput(
            func=process_audio,
            content_types=[ContentType.AUDIO],
        ),
        state=MenuSG.main,
    ),
)

router.include_routers(menu_dialog)
