import logging
import re
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
FEAT_LIST = {"feat", "feat.", "ft.", ","}
ARTIST_SPLIT_T = f"(?:{'|'.join(FEAT_LIST)})"


async def process_query(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    logger.info("Hello!")


async def process_audio(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    album: Album = dialog_manager.middleware_data["album"]
    bot: Bot = dialog_manager.middleware_data["bot"]

    for audio in album.audio:
        with BytesIO() as track_file:
            file_data = await bot.get_file(audio.file_id)
            await bot.download_file(file_data.file_path, destination=track_file)
            audio_bytes = track_file.read()
            track_file.seek(0)
            if audio.thumbnail:
                with BytesIO() as cover_f:
                    cover_data = await bot.get_file(audio.thumbnail.file_id)
                    await bot.download_file(cover_data.file_path, destination=cover_f)
                    cover_bytes = cover_f.read()

            tags = MP3(track_file)
            artist = re.split(ARTIST_SPLIT_T, tags.get("TPE1").text[0])[0].strip()
            artist_path = config.download_path / artist
            tags.pop("APIC:")
            print(tags)
            artist_path.mkdir(parents=True, exist_ok=True)
            if audio.thumbnail:
                cover_path = artist_path / "cover.jpg"
                with cover_path.open("wb") as cover_file:
                    cover_file.write(cover_bytes)

            track_path = artist_path / (tags.get("TIT2").text[0] + ".mp3")
            with track_path.open("wb") as audio_file:
                audio_file.write(audio_bytes)

            # tags["APIC"] = APIC(
            #     encoding=3,
            #     mime="image/jpeg",
            #     type=3, desc=u"Cover",
            #     data=cover_bytes,
            # )
            tags.save(track_path)


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
