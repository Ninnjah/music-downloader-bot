import httpx
from celery import Task
from tgbot.config_reader import config


class NotificationTask(Task):
    ENDPOINT = "note"
    NOTE_SERVER = f"http://{config.server.host}:{config.server.port}/{{endpoint}}"

    def on_success(self, retval, task_id, args, kwargs):
        payload = {
            "user_id": args[0],
            "task_id": task_id,
            "status": "SUCCESS",
            "info": retval,
        }
        httpx.post(self.NOTE_SERVER.format(endpoint=self.ENDPOINT), json=payload)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        payload = {
            "user_id": args[0],
            "task_id": task_id,
            "status": "FAIL",
            "info": repr(exc),
        }
        httpx.post(self.NOTE_SERVER.format(endpoint=self.ENDPOINT), json=payload)
