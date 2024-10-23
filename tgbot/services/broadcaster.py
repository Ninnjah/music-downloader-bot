import asyncio
import logging
from typing import List, Optional, Sequence, Union

from aiogram import Bot, exceptions
from aiogram.types import (
    ContentType,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

logger = logging.getLogger(__name__)


async def send_message(
    bot: Bot,
    user_id: Union[int, str],
    text: Optional[str] = None,
    media_group: Optional[
        List[Union[InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument]]
    ] = None,
    disable_notification: bool = False,
    reply_markup: InlineKeyboardMarkup = None,
) -> bool:
    """
    Safe messages sender

    :param bot: Bot instance.
    :param user_id: user id. If str - must contain only digits.
    :param text: text of the message.
    :param media_group: List of input media.
    :param disable_notification: disable notification or not.
    :param reply_markup: reply markup.
    :return: success.
    """
    try:
        if text:
            await bot.send_message(
                user_id,
                text,
                disable_notification=disable_notification,
                reply_markup=reply_markup,
            )
        elif media_group and reply_markup:
            media = media_group[0]
            if media.type == ContentType.PHOTO:
                await bot.send_photo(
                    user_id,
                    media.media,
                    caption=text,
                    disable_notification=disable_notification,
                    reply_markup=reply_markup,
                )
            if media.type == ContentType.VIDEO:
                await bot.send_video(
                    user_id,
                    media.media,
                    caption=text,
                    disable_notification=disable_notification,
                    reply_markup=reply_markup,
                )
        elif media_group:
            await bot.send_media_group(
                user_id,
                media=media_group,
            )
    except exceptions.TelegramBadRequest:
        logger.error("Telegram server says - Bad Request: chat not found")
    except exceptions.TelegramForbiddenError:
        logger.error(f"Target [ID:{user_id}]: got TelegramForbiddenError")
    except exceptions.TelegramRetryAfter as e:
        logger.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        return await send_message(
            bot, user_id, text, media_group, disable_notification, reply_markup
        )  # Recursive call
    except exceptions.TelegramAPIError:
        logger.exception(f"Target [ID:{user_id}]: failed")
    else:
        logger.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcast(
    bot: Bot,
    users: Sequence[Union[str, int]],
    text: Optional[str],
    media_group: List[Union[InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument]] = [],
    disable_notification: bool = False,
    reply_markup: InlineKeyboardMarkup = None,
) -> int:
    """
    Simple broadcaster.
    :param bot: Bot instance.
    :param users: List of users.
    :param text: Text of the message. Must be empty if media_group is using
    :param media_group: List of input media. Must be empty if text is using
    :param disable_notification: Disable notification or not.
    :param reply_markup: Reply markup.
    :return: Count of messages.
    """
    if (text and media_group) or (not text and not media_group):
        raise ValueError("Text or media group must be set")

    count = 0
    try:
        for user_id in users:
            if await send_message(bot, user_id, text, media_group, disable_notification, reply_markup):
                count += 1
            await asyncio.sleep(0.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logger.info(f"{count} messages successful sent.")

    return count
