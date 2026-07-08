"""arq (Redis) queue helpers. Job types + retry policy defined in workers/main.py."""
from __future__ import annotations

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings

_settings = get_settings()


def redis_settings() -> RedisSettings:
    return RedisSettings(host=_settings.redis_host, port=_settings.redis_port)


async def get_queue() -> ArqRedis:
    return await create_pool(redis_settings())
