from aiogram import Router

from . import admin, commands, user

__all__ = ("main_router",)

main_router = Router(name=__name__)

main_router.include_routers(
    commands.router,
    admin.router,
    user.router,
)
