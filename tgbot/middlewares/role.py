from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tgbot.models.role import UserRole


class RoleMiddleware(BaseMiddleware):
    def __init__(self, admin_list: List[int]):
        self.admin_list = admin_list

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        roles = []
        repo = data["repo"]

        if not getattr(event, "from_user", None):
            data["roles"] = None

        else:
            roles.append(UserRole.USER)
            admin = await repo.get_admin(event.from_user.id)

            role_filters = {
                UserRole.ADMIN: admin is not None,
                UserRole.SUDO: any((event.from_user.id in self.admin_list, admin and admin.sudo)),
            }

            for role, filter_ in role_filters.items():
                if filter_:
                    roles.append(role)

        data["roles"] = roles

        result = await handler(event, data)

        del data["roles"]
        return result
