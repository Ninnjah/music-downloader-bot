from celery import Celery
from yandex_music import Client
from tgbot.config_reader import config

BROKER_PREFIX = "tasker"
redis_password = f":{config.redis.password}@" if config.redis.password else ""
REDIS_URL = f"redis://{redis_password}{config.redis.host}:{config.redis.port}/{config.redis.db}"

app = Celery(
    BROKER_PREFIX,
    broker=REDIS_URL,
    backend=REDIS_URL,
)
app.config_from_object("celeryconfig")
