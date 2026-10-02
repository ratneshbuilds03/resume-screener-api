import json

import redis

from app.config import settings


def get_redis():
    try:
        return redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            protocol=2,
        )
    except Exception:
        return None


def cache_set(key: str, data, expire_seconds: int = 3600):
    client = get_redis()
    if client is None:
        return False

    try:
        client.setex(key, expire_seconds, json.dumps(data))
        return True
    except Exception:
        return False


def cache_get(key: str):
    client = get_redis()
    if client is None:
        return None

    try:
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


def cache_delete(key: str):
    client = get_redis()
    if client is None:
        return False

    try:
        return bool(client.delete(key))
    except Exception:
        return False