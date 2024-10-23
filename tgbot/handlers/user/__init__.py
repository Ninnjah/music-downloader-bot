from aiogram import Router

from . import start

__all__ = ("router",)

router = Router(name=__name__)

router.include_routers(
    start.router,
)
