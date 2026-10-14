from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DuplicateEventException
from app.integrations.redis.client import RedisCache
from app.schemas.event import EventCreate
from app.services.event_service import DEDUP_PREFIX


@pytest.fixture
def event_payload():
    return EventCreate(
        event_id="evt-unit-001",
        event_type="user_login",
        user_id="user-1",
        source="web",
        metadata={"ip": "127.0.0.1"},
        timestamp=datetime.now(tz=timezone.utc),
    )


@pytest.mark.asyncio
async def test_deduplication_raises_on_duplicate(event_payload):
    """EventService should raise DuplicateEventException for repeated event_id."""
    from app.services.event_service import EventService

    mock_cache = AsyncMock(spec=RedisCache)
    mock_cache.exists.return_value = True  # Simulate existing key

    mock_db = AsyncMock()
    svc = EventService(db=mock_db, cache=mock_cache)

    with pytest.raises(DuplicateEventException):
        await svc.ingest_event(event_payload)

    mock_cache.exists.assert_called_once_with(f"{DEDUP_PREFIX}{event_payload.event_id}")


@pytest.mark.asyncio
async def test_dedup_key_stored_after_ingest(event_payload):
    """After successful ingestion, event_id should be stored in Redis."""
    from app.services.event_service import EventService
    from app.repositories.event_repository import EventRepository

    mock_cache = AsyncMock(spec=RedisCache)
    mock_cache.exists.return_value = False  # Not a duplicate

    # Mock the repo
    fake_event = MagicMock()
    fake_event.event_id = event_payload.event_id

    mock_repo = AsyncMock(spec=EventRepository)
    mock_repo.create.return_value = fake_event

    mock_db = AsyncMock()
    svc = EventService(db=mock_db, cache=mock_cache)
    svc.repo = mock_repo

    result = await svc.ingest_event(event_payload)

    mock_cache.set.assert_any_call(
        f"{DEDUP_PREFIX}{event_payload.event_id}",
        {"event_id": event_payload.event_id},
        ttl=604_800,
    )
    assert result == fake_event


@pytest.mark.asyncio
async def test_cache_invalidated_on_ingest(event_payload):
    """Analytics caches must be invalidated after ingesting an event."""
    from app.services.event_service import EventService
    from app.repositories.event_repository import EventRepository

    mock_cache = AsyncMock(spec=RedisCache)
    mock_cache.exists.return_value = False

    fake_event = MagicMock()
    mock_repo = AsyncMock(spec=EventRepository)
    mock_repo.create.return_value = fake_event

    mock_db = AsyncMock()
    svc = EventService(db=mock_db, cache=mock_cache)
    svc.repo = mock_repo

    await svc.ingest_event(event_payload)

    mock_cache.delete.assert_called_once_with(
        "analytics:daily",
        "analytics:monthly",
        "analytics:summary",
        "analytics:top_sources",
    )
