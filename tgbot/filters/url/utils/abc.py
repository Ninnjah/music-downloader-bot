from typing import Dict, Iterable, Literal, Union

from aiogram.enums import MessageEntityType
from aiogram.filters import Filter
from aiogram.types import Message

from .types import UrlList


class UrlFilterProtocol(Filter):
    @staticmethod
    async def extract_urls(message: Message) -> Iterable[str]:
        return [
            e.extract_from(message.text).strip("/")
            for e in message.entities or []
            if e.type == MessageEntityType.URL
        ]

    async def __call__(self, message: Message) -> Union[bool, Dict[Literal["urls"], UrlList]]:
        raise NotImplementedError
