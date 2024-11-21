from uuid import uuid4


def generate_task_id(*data, sep: str = "_") -> str:
    return sep.join(map(str, [*data, uuid4().hex[-12:]]))
