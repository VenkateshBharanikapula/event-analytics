from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.redis.client import RedisCache
from app.schemas.analytics import DailyAnalytics


@pytest.mark.asyncio
async def test_redis_cache_set_and_get():
    """RedisCache should store and retrieve JSON data."""
    import fakeredis.aioredis as fr
    redis = fr.FakeRedis(decode_responses=True)
    cache = RedisCache(redis)

    await cache.set("test:key", {"value": 42}, ttl=60)
    result = await cache.get("test:key")

    assert result == {"value": 42}
    await redis.aclose()


@pytest.mark.asyncio
async def test_redis_cache_miss_returns_none():
    import fakeredis.aioredis as fr
    redis = fr.FakeRedis(decode_responses=True)
    cache = RedisCache(redis)

    result = await cache.get("nonexistent:key")
    assert result is None
    await redis.aclose()


@pytest.mark.asyncio
async def test_redis_cache_delete():
    import fakeredis.aioredis as fr
    redis = fr.FakeRedis(decode_responses=True)
    cache = RedisCache(redis)

    await cache.set("del:key", {"x": 1})
    await cache.delete("del:key")
    result = await cache.get("del:key")

    assert result is None
    await redis.aclose()


@pytest.mark.asyncio
async def test_analytics_daily_uses_cache():
    """AnalyticsService should return cached data without hitting the DB."""
    from app.services.analytics_service import AnalyticsService

    mock_cache = AsyncMock(spec=RedisCache)
    mock_cache.get.return_value = {
        "data": [{"date": "2024-01-01", "count": 5}],
        "total_days": 1,
    }

    mock_db = AsyncMock()
    svc = AnalyticsService(db=mock_db, cache=mock_cache)

    result = await svc.get_daily()

    mock_cache.get.assert_called_once_with("analytics:daily")
    assert isinstance(result, DailyAnalytics)
    assert result.total_days == 1


@pytest.mark.asyncio
async def test_analytics_daily_populates_cache_on_miss():
    """AnalyticsService should query DB and populate cache on cache miss."""
    from app.services.analytics_service import AnalyticsService
    from app.selectors.analytics_selector import AnalyticsSelector

    mock_cache = AsyncMock(spec=RedisCache)
    mock_cache.get.return_value = None  # Cache miss

    mock_selector = AsyncMock(spec=AnalyticsSelector)
    mock_selector.get_daily_counts.return_value = [{"date": "2024-01-01", "count": 10}]

    mock_db = AsyncMock()
    svc = AnalyticsService(db=mock_db, cache=mock_cache)
    svc.selector = mock_selector

    result = await svc.get_daily()

    mock_selector.get_daily_counts.assert_called_once()
    mock_cache.set.assert_called_once()
    assert result.total_days == 1
