from contextlib import suppress
from dataclasses import dataclass
from typing import Iterable, List

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from fluent.runtime import FluentLocalization


@dataclass(frozen=True)
class Commands:
    user: List[BotCommand]
    admin: List[BotCommand]


def get_commands(l10n: FluentLocalization) -> Commands:
    command_list = [BotCommand(command="start", description=l10n.format_value("command-start"))]
    admin_command_list = command_list + [
        BotCommand(command="admin", description=l10n.format_value("command-admin"))
    ]

    return Commands(
        user=command_list,
        admin=admin_command_list,
    )


async def register_commands(bot: Bot, l10n: FluentLocalization, admin_list: Iterable[int]):
    commands = get_commands(l10n)

    with suppress(TelegramBadRequest):
        for admin_id in admin_list:
            await bot.set_my_commands(
                commands.admin,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )

    await bot.set_my_commands(commands.user, scope=BotCommandScopeDefault())
