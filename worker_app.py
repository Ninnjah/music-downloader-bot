from uuid import uuid4

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from taskiq import SimpleRetryMiddleware
from taskiq_redis import ListQueueBroker

from worker.middleware.base_depends import DependsMiddleware
from worker.middleware.notification import YandexNoteMiddleware, SpotifyNoteMiddleware
from worker.middleware.task_id import CustomTaskIDMiddleware
from worker.services.result_backend import RedisResultBackend
from tgbot.config_reader import config
from tgbot.fluent_loader import get_fluent_localization

BROKER_PREFIX = f"{config.redis.prefix}:broker"
redis_password = f":{config.redis.password}@" if config.redis.password else ""
REDIS_URL = f"redis://{redis_password}{config.redis.host}:{config.redis.port}/{config.redis.db}"


def id_generator() -> str:
    return f"{BROKER_PREFIX}:{uuid4().hex}"


broker = (
    ListQueueBroker(url=REDIS_URL)
    .with_id_generator(id_generator)
    .with_result_backend(RedisResultBackend(redis_url=REDIS_URL))
    .with_middlewares(
        SimpleRetryMiddleware(default_retry_count=3),
        DependsMiddleware(
            bot=Bot(
                token=config.bot_token,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML,
                    link_preview_is_disabled=True,
                ),
            ),
            l10n=get_fluent_localization(),
        ),
        YandexNoteMiddleware(),
        SpotifyNoteMiddleware(),
        CustomTaskIDMiddleware(),
    )
)
