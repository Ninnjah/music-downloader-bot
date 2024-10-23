import asyncio
import logging
from typing import Tuple

import redis.asyncio as redis

from aiohttp.web import run_app
from aiohttp.web_app import Application

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.enums.parse_mode import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from aiogram_dialog import setup_dialogs

from tgbot.config_reader import config
from tgbot.fluent_loader import get_fluent_localization
from tgbot.handlers import main_router
from tgbot.middlewares.media_group import AlbumMiddleware
from tgbot.middlewares.role import RoleMiddleware
from tgbot.middlewares.throttling import ThrottlingMiddleware

logger = logging.getLogger(__name__)


def setup_logger(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


def setup_bot() -> Tuple[Dispatcher, Bot]:
    config.download_path.mkdir(parents=True, exist_ok=True)

    if config.redis.enabled:
        storage = RedisStorage(
            redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
            ),
            key_builder=DefaultKeyBuilder(prefix=config.redis.prefix, with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
    dp = Dispatcher(storage=storage)
    l10n = get_fluent_localization()
    dp["base_url"] = config.webhook.url
    dp["webhook_path"] = config.webhook.path
    dp["admin_list"] = config.admin_list
    dp["l10n"] = l10n

    dp.message.outer_middleware(AlbumMiddleware())
    dp.message.outer_middleware(RoleMiddleware(config.admin_list))
    dp.callback_query.outer_middleware(RoleMiddleware(config.admin_list))
    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.callback_query.outer_middleware(ThrottlingMiddleware())

    dp.include_router(main_router)
    setup_dialogs(dp)

    return dp, bot


async def on_startup(bot: Bot, base_url: str, webhook_path: str):
    if logging.root.level <= logging.INFO and config.webhook.enabled:
        bot_info = await bot.get_me()
        logger.info(
            "Run webhook for bot @%s id=%d - '%s'",
            bot_info.username,
            bot_info.id,
            bot_info.full_name,
        )

    await bot.delete_webhook(drop_pending_updates=True)
    if config.webhook.enabled:
        logger.info("WEBHOOK_URL - %s", f"{base_url}{webhook_path}")
        await bot.set_webhook(f"{base_url}{webhook_path}")


def start_webhook(dp: Dispatcher, bot: Bot):
    app = Application()
    app["bot"] = bot
    app["base_url"] = config.webhook.url

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    run_app(app, host="127.0.0.1", port=config.webhook.port)


async def start_polling(dp: Dispatcher, bot: Bot):
    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


def main():
    setup_logger()
    logger.error("Starting bot (It's not an ERROR)")

    dp, bot = setup_bot()
    dp.startup.register(on_startup)

    if config.webhook.enabled:
        start_webhook(dp, bot)
    else:
        asyncio.run(start_polling(dp, bot))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
