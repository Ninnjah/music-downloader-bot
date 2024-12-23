import logging
from typing import Any, Coroutine, Union

from taskiq import TaskiqMessage, TaskiqMiddleware

logger = logging.getLogger(__name__)


class CustomTaskIDMiddleware(TaskiqMiddleware):
    async def pre_send(
        self,
        message: "TaskiqMessage",
    ) -> "Union[TaskiqMessage, Coroutine[Any, Any, TaskiqMessage]]":
        if task_id := message.kwargs.get("task_id"):
            message.task_id = task_id
        return message
