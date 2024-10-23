from aiogram import Router

from . import commands, user

__all__ = ("main_router",)

main_router = Router(name=__name__)

main_router.include_routers(
    commands.router,
    user.router,
)
