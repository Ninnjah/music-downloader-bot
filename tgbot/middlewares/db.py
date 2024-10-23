from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from tgbot.services.repository import Repo


class DbMiddleware(BaseMiddleware):
    def __init__(self, pool: AsyncEngine):
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async_session = async_sessionmaker(self.pool, expire_on_commit=False)
        async with async_session() as session:
            repo = Repo(session)
            data["repo"] = repo

            result = await handler(event, data)

            del data["repo"]
            return result
