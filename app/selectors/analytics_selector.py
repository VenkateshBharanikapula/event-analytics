from datetime import datetime

from sqlalchemy import func, select, extract, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus


class AnalyticsSelector:
    """Encapsulates all analytics SQL queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_counts(self, limit: int = 30) -> list[dict]:
        result = await self.db.execute(
            select(
                cast(Event.timestamp, Date).label("date"),
                func.count(Event.id).label("count"),
            )
            .where(Event.status == EventStatus.ACTIVE)
            .group_by(cast(Event.timestamp, Date))
            .order_by(cast(Event.timestamp, Date).desc())
            .limit(limit)
        )
        return [{"date": str(row.date), "count": row.count} for row in result]

    async def get_monthly_counts(self, limit: int = 12) -> list[dict]:
        result = await self.db.execute(
            select(
                extract("year", Event.timestamp).label("year"),
                extract("month", Event.timestamp).label("month"),
                func.count(Event.id).label("count"),
            )
            .where(Event.status == EventStatus.ACTIVE)
            .group_by(
                extract("year", Event.timestamp),
                extract("month", Event.timestamp),
            )
            .order_by(
                extract("year", Event.timestamp).desc(),
                extract("month", Event.timestamp).desc(),
            )
            .limit(limit)
        )
        rows = [
            {
                "month": f"{int(row.year):04d}-{int(row.month):02d}",
                "count": row.count,
            }
            for row in result
        ]
        return rows

    async def get_event_type_distribution(self) -> list[dict]:
        result = await self.db.execute(
            select(
                Event.event_type,
                func.count(Event.id).label("count"),
            )
            .where(Event.status == EventStatus.ACTIVE)
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
        )
        return [{"event_type": row.event_type, "count": row.count} for row in result]

    async def get_top_sources(self, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(
                Event.source,
                func.count(Event.id).label("count"),
            )
            .where(Event.status == EventStatus.ACTIVE)
            .group_by(Event.source)
            .order_by(func.count(Event.id).desc())
            .limit(limit)
        )
        return [{"source": row.source, "count": row.count} for row in result]

    async def get_total_count(self) -> int:
        result = await self.db.execute(select(func.count(Event.id)))
        return result.scalar_one()

    async def get_count_by_status(self, status: EventStatus) -> int:
        result = await self.db.execute(
            select(func.count(Event.id)).where(Event.status == status)
        )
        return result.scalar_one()

    async def get_counts_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                cast(Event.timestamp, Date).label("date"),
                func.count(Event.id).label("count"),
            )
            .where(
                Event.status == EventStatus.ACTIVE,
                Event.timestamp >= start_date,
                Event.timestamp <= end_date,
            )
            .group_by(cast(Event.timestamp, Date))
            .order_by(cast(Event.timestamp, Date).asc())
        )
        return [{"date": str(row.date), "count": row.count} for row in result]

    async def get_event_types_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                Event.event_type,
                func.count(Event.id).label("count"),
            )
            .where(
                Event.status == EventStatus.ACTIVE,
                Event.timestamp >= start_date,
                Event.timestamp <= end_date,
            )
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
        )
        return [{"event_type": row.event_type, "count": row.count} for row in result]

    async def get_sources_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict]:
        result = await self.db.execute(
            select(
                Event.source,
                func.count(Event.id).label("count"),
            )
            .where(
                Event.status == EventStatus.ACTIVE,
                Event.timestamp >= start_date,
                Event.timestamp <= end_date,
            )
            .group_by(Event.source)
            .order_by(func.count(Event.id).desc())
        )
        return [{"source": row.source, "count": row.count} for row in result]
