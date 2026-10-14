import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DuplicateEventException, EventNotFoundException
from app.integrations.redis.client import RedisCache
from app.integrations.s3.client import S3Client
from app.repositories.event_repository import EventRepository
from app.schemas.event import ArchiveResponse, EventCreate, EventListParams, PaginatedEvents

logger = logging.getLogger(__name__)

DEDUP_PREFIX = "dedup:event:"


class EventService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.repo = EventRepository(db)
        self.cache = cache

    async def ingest_event(self, data: EventCreate):
        dedup_key = f"{DEDUP_PREFIX}{data.event_id}"

        # Deduplication check via Redis
        if await self.cache.exists(dedup_key):
            logger.warning("Duplicate event detected: %s", data.event_id)
            raise DuplicateEventException(data.event_id)

        event = await self.repo.create(data)

        # Mark in Redis — keep for 7 days to prevent replay attacks
        await self.cache.set(dedup_key, {"event_id": data.event_id}, ttl=604_800)

        # Invalidate analytics caches
        await self.cache.delete(
            "analytics:daily",
            "analytics:monthly",
            "analytics:summary",
            "analytics:top_sources",
        )
        logger.info("Event ingested: %s", data.event_id)
        return event

    async def get_event(self, event_id: str):
        event = await self.repo.get_by_event_id(event_id)
        if not event:
            raise EventNotFoundException(event_id)
        return event

    async def list_events(self, params: EventListParams) -> PaginatedEvents:
        items, total = await self.repo.list_events(params)
        return PaginatedEvents(
            total=total,
            page=params.page,
            page_size=params.page_size,
            items=items,
        )

    async def archive_old_events(self, s3: S3Client) -> ArchiveResponse:
        threshold = settings.ARCHIVE_DAYS_THRESHOLD
        old_events = await self.repo.get_active_events_older_than(threshold)

        if not old_events:
            return ArchiveResponse(
                message="No events to archive.", archived_count=0, s3_path=""
            )

        # Serialize
        payload = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "user_id": e.user_id,
                "source": e.source,
                "metadata": e.metadata_,
                "timestamp": e.timestamp.isoformat(),
                "status": e.status,
            }
            for e in old_events
        ]

        archive_date = datetime.utcnow()
        key = s3.build_archive_key(archive_date)
        s3_path = s3.upload_json(payload, key)

        ids = [e.id for e in old_events]
        await self.repo.mark_as_archived(ids)
        await self.repo.create_archive_record(s3_path, len(ids), archive_date)

        # Invalidate caches
        await self.cache.delete(
            "analytics:daily",
            "analytics:monthly",
            "analytics:summary",
            "analytics:top_sources",
        )

        logger.info("Archived %d events → %s", len(ids), s3_path)
        return ArchiveResponse(
            message=f"Archived {len(ids)} events.", archived_count=len(ids), s3_path=s3_path
        )

    async def get_archives(self):
        return await self.repo.get_archives()
