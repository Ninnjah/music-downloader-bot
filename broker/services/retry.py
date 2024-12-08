import time
import logging

logger = logging.getLogger(__name__)


def retry(attempt_count: int = 3, timeout: float = 1):
    def decorator(f):
        def wrapper(*args, **kwargs):
            for attempt in range(attempt_count):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if attempt + 1 == attempt_count:
                        logger.warning("retry - %s", e)
                    else:
                        time.sleep(timeout)
        return wrapper
    return decorator
