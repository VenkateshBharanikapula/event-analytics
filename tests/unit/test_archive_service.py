from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest


def test_s3_build_archive_key():
    from app.integrations.s3.client import S3Client
    dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
    key = S3Client.build_archive_key(dt)
    assert key == "archives/2024/03/15/events_103000.json"


@patch("app.integrations.s3.client.boto3.client")
def test_s3_upload_json(mock_boto):
    from app.integrations.s3.client import S3Client

    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    client = S3Client()
    client._bucket = "test-bucket"

    data = [{"event_id": "e1", "event_type": "login"}]
    path = client.upload_json(data, "archives/test.json")

    mock_s3.put_object.assert_called_once()
    assert "s3://test-bucket/archives/test.json" == path


@pytest.mark.asyncio
async def test_archive_service_no_events():
    """Archive should return 0 when there are no old events."""
    from app.services.event_service import EventService
    from app.integrations.redis.client import RedisCache
    from app.repositories.event_repository import EventRepository

    mock_cache = AsyncMock = MagicMock()
    mock_cache.exists = MagicMock(return_value=False)

    mock_repo = MagicMock(spec=EventRepository)
    mock_repo.get_active_events_older_than = MagicMock(return_value=[])

    import asyncio

    async def async_return(val):
        return val

    mock_repo.get_active_events_older_than = lambda _: async_return([])

    from app.integrations.redis.client import RedisCache
    from unittest.mock import AsyncMock

    cache_mock = AsyncMock(spec=RedisCache)

    mock_db = MagicMock()
    svc = EventService(db=mock_db, cache=cache_mock)
    svc.repo = mock_repo

    mock_s3 = MagicMock()
    result = await svc.archive_old_events(mock_s3)

    assert result.archived_count == 0
    assert result.message == "No events to archive."
