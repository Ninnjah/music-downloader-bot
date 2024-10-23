from aiogram.filters import Filter
from aiogram.types import Message
from fluent.runtime import FluentLocalization


class TextFilter(Filter):
    def __init__(self, text: str) -> None:
        self.text = text

    async def __call__(self, message: Message, l10n: FluentLocalization) -> bool:
        return message.text == l10n.format_value(self.text)
