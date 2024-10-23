from typing import Collection, List, Union

from aiogram.filters import Filter
from aiogram.types import User

from tgbot.models.role import UserRole


class RoleFilter(Filter):
    def __init__(self, role: Union[UserRole, Collection[UserRole]]) -> None:
        if isinstance(role, UserRole):
            self.roles = {role}
        else:
            self.roles = set(role)

    async def __call__(
        self,
        *args,
        event_from_user: User,
        admin_list: List[int],
        roles: Union[None, Collection[UserRole]] = None,
        **kwargs,
    ) -> bool:
        return any((role for role in roles if role in self.roles))


class IsSudoFilter(RoleFilter):
    def __init__(self) -> None:
        super().__init__(UserRole.SUDO)


class IsAdminFilter(IsSudoFilter):
    def __init__(self) -> None:
        super().__init__()
        self.roles.add(UserRole.ADMIN)
