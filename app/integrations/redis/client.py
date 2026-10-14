import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


class RedisCache:
    """Thin wrapper around Redis for caching JSON-serialisable data."""

    def __init__(self, client: aioredis.Redis):
        self._client = client

    async def get(self, key: str) -> Any | None:
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
        except Exception as exc:
            logger.warning("Cache GET failed for key '%s': %s", key, exc)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            await self._client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as exc:
            logger.warning("Cache SET failed for key '%s': %s", key, exc)

    async def delete(self, *keys: str) -> None:
        try:
            await self._client.delete(*keys)
        except Exception as exc:
            logger.warning("Cache DELETE failed: %s", exc)

    async def exists(self, key: str) -> bool:
        try:
            return bool(await self._client.exists(key))
        except Exception as exc:
            logger.warning("Cache EXISTS failed for key '%s': %s", key, exc)
            return False
