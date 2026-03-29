import time
from threading import Lock

import redis

from app.core.config import settings
from app.core.exceptions import RateLimitExceeded

_redis_client = None


class _InMemoryRedis:
    def __init__(self):
        self.store = {}
        self.expiry = {}
        self.lock = Lock()

    def _purge(self, key: str):
        expiry = self.expiry.get(key)
        if expiry is not None and expiry <= time.time():
            self.store.pop(key, None)
            self.expiry.pop(key, None)

    def incr(self, key: str) -> int:
        with self.lock:
            self._purge(key)
            self.store[key] = int(self.store.get(key, 0)) + 1
            return self.store[key]

    def expire(self, key: str, seconds: int):
        with self.lock:
            self.expiry[key] = time.time() + seconds

    def delete(self, key: str):
        with self.lock:
            self.store.pop(key, None)
            self.expiry.pop(key, None)


_fallback = _InMemoryRedis()


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            _redis_client.ping()
        except Exception:
            _redis_client = _fallback
    return _redis_client


def check_login_attempt(key: str) -> None:
    client = get_redis_client()
    count = int(client.incr(key))
    if count == 1:
        client.expire(key, settings.login_rate_limit_window_seconds)
    if count > settings.login_rate_limit_max_attempts:
        raise RateLimitExceeded('Too many login attempts. Please try again later.')



def clear_login_attempts(key: str) -> None:
    get_redis_client().delete(key)
