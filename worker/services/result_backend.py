from typing import Dict, Union

from redis.asyncio import Redis

from taskiq import TaskiqResult
from taskiq.compat import model_dump
from taskiq_redis import RedisAsyncResultBackend
from taskiq_redis.redis_backend import _ReturnType

from yandex_music import YandexMusicObject


class RedisResultBackend(RedisAsyncResultBackend):
    async def set_result(
        self,
        task_id: str,
        result: TaskiqResult[_ReturnType],
    ) -> None:
        """
        Sets task result in redis.

        Dumps TaskiqResult instance into the bytes and writes
        it to redis.

        :param task_id: ID of the task.
        :param result: TaskiqResult instance.
        """
        if isinstance(result.return_value, YandexMusicObject):
            result.return_value = result.return_value.to_dict()

        redis_set_params: Dict[str, Union[str, int, bytes]] = {
            "name": task_id,
            "value": self.serializer.dumpb(model_dump(result)),
        }
        if self.result_ex_time:
            redis_set_params["ex"] = self.result_ex_time
        elif self.result_px_time:
            redis_set_params["px"] = self.result_px_time

        async with Redis(connection_pool=self.redis_pool) as redis:
            await redis.set(**redis_set_params)  # type: ignore

