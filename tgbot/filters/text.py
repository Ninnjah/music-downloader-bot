from typing import Any, Dict, Union

from aiogram.enums import MessageEntityType
from aiogram.filters import Filter
from aiogram.types import Message

from fluent.runtime import FluentLocalization


class TextFilter(Filter):
    def __init__(self, text: str) -> None:
        self.text = text

    async def __call__(self, message: Message, l10n: FluentLocalization) -> bool:
        return message.text == l10n.format_value(self.text)


class UrlFilter(Filter):
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        urls = [
            e.extract_from(message.text).strip("/")
            for e in message.entities or []
            if e.type == MessageEntityType.URL
        ]

        if len(urls) > 0:
            return {"urls": urls}
        else:
            return False
