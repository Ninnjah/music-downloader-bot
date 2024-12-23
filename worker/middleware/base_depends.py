import logging

from aiogram import Bot
from fluent.runtime import FluentLocalization
from taskiq import TaskiqMessage, TaskiqMiddleware

logger = logging.getLogger(__name__)


class DependsMiddleware(TaskiqMiddleware):
    def __init__(self, bot: Bot, l10n: FluentLocalization):
        super().__init__()
        self.bot = bot
        self.l10n = l10n

    async def pre_execute(self, message: "TaskiqMessage") -> TaskiqMessage:
        message.kwargs.update({"bot": self.bot, "l10n": self.l10n})
        return message
