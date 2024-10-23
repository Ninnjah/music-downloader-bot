from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get(link_list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for link in link_list:
        keyboard.button(text=link[0], url=link[1])

    keyboard.adjust(1)

    return keyboard.as_markup()
