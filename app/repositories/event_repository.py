from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event, EventArchive, EventCategory, EventStatus
from app.schemas.event import EventCreate, EventListParams


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: EventCreate) -> Event:
        event = Event(
            event_id=data.event_id,
            event_type=data.event_type,
            user_id=data.user_id,
            source=data.source,
            metadata_=data.metadata,
            timestamp=data.timestamp,
            category_id=data.category_id,
            status=EventStatus.ACTIVE,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_by_event_id(self, event_id: str) -> Event | None:
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.category))
            .where(Event.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id_: int) -> Event | None:
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.category))
            .where(Event.id == id_)
        )
        return result.scalar_one_or_none()

    async def list_events(self, params: EventListParams) -> tuple[list[Event], int]:
        query = (
            select(Event)
            .options(selectinload(Event.category))
            .where(Event.status == EventStatus.ACTIVE)
        )

        if params.event_type:
            query = query.where(Event.event_type == params.event_type)
        if params.category_id:
            query = query.where(Event.category_id == params.category_id)
        if params.source:
            query = query.where(Event.source == params.source)
        if params.start_date:
            query = query.where(Event.timestamp >= params.start_date)
        if params.end_date:
            query = query.where(Event.timestamp <= params.end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Sort
        sort_col = getattr(Event, params.sort_by, Event.timestamp)
        if params.sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Paginate
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_active_events_older_than(self, days: int) -> list[Event]:
        cutoff = datetime.utcnow()
        from datetime import timedelta
        cutoff -= timedelta(days=days)
        result = await self.db.execute(
            select(Event).where(
                Event.status == EventStatus.ACTIVE,
                Event.timestamp < cutoff,
            )
        )
        return result.scalars().all()

    async def mark_as_archived(self, event_ids: list[int]) -> None:
        await self.db.execute(
            update(Event)
            .where(Event.id.in_(event_ids))
            .values(status=EventStatus.ARCHIVED)
        )
        await self.db.commit()

    async def create_archive_record(
        self, s3_path: str, count: int, archive_date: datetime
    ) -> EventArchive:
        record = EventArchive(
            s3_file_path=s3_path,
            events_count=count,
            archive_date=archive_date,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_archives(self) -> list[EventArchive]:
        result = await self.db.execute(
            select(EventArchive).order_by(EventArchive.archive_date.desc())
        )
        return result.scalars().all()


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, description: str | None) -> EventCategory:
        cat = EventCategory(name=name, description=description)
        self.db.add(cat)
        await self.db.commit()
        await self.db.refresh(cat)
        return cat

    async def get_all(self) -> list[EventCategory]:
        result = await self.db.execute(select(EventCategory).order_by(EventCategory.name))
        return result.scalars().all()

    async def get_by_id(self, id_: int) -> EventCategory | None:
        result = await self.db.execute(
            select(EventCategory).where(EventCategory.id == id_)
        )
        return result.scalar_one_or_none()
