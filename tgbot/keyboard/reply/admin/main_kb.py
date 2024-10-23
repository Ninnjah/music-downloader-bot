from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import KeyboardButton, ReplyKeyboardBuilder
from fluent.runtime import FluentLocalization

from tgbot.models.role import UserRole


def get(l10n: FluentLocalization, roles) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(KeyboardButton(text=l10n.format_value("admin-button-list-users")))

    if UserRole.SUDO in roles:
        keyboard.row(KeyboardButton(text=l10n.format_value("admin-button-list-admins")))

    return keyboard.as_markup(resize_keyboard=True)
