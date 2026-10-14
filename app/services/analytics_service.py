import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.redis.client import RedisCache
from app.models.event import EventStatus
from app.selectors.analytics_selector import AnalyticsSelector
from app.schemas.analytics import (
    CustomReport,
    DailyAnalytics,
    EventTypeDistribution,
    MonthlyAnalytics,
    SummaryReport,
    TopSources,
    TrendsReport,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.selector = AnalyticsSelector(db)
        self.cache = cache

    async def get_daily(self) -> DailyAnalytics:
        cached = await self.cache.get("analytics:daily")
        if cached:
            return DailyAnalytics(**cached)

        data = await self.selector.get_daily_counts()
        result = DailyAnalytics(data=data, total_days=len(data))
        await self.cache.set("analytics:daily", result.model_dump(), ttl=settings.CACHE_TTL_DAILY)
        return result

    async def get_monthly(self) -> MonthlyAnalytics:
        cached = await self.cache.get("analytics:monthly")
        if cached:
            return MonthlyAnalytics(**cached)

        data = await self.selector.get_monthly_counts()
        result = MonthlyAnalytics(data=data, total_months=len(data))
        await self.cache.set("analytics:monthly", result.model_dump(), ttl=settings.CACHE_TTL_MONTHLY)
        return result

    async def get_event_types(self) -> EventTypeDistribution:
        data = await self.selector.get_event_type_distribution()
        return EventTypeDistribution(data=data, total_types=len(data))

    async def get_top_sources(self) -> TopSources:
        cached = await self.cache.get("analytics:top_sources")
        if cached:
            return TopSources(**cached)

        data = await self.selector.get_top_sources()
        result = TopSources(data=data, total_sources=len(data))
        await self.cache.set("analytics:top_sources", result.model_dump(), ttl=settings.CACHE_TTL_TOP_SOURCES)
        return result

    async def get_summary(self) -> SummaryReport:
        cached = await self.cache.get("analytics:summary")
        if cached:
            return SummaryReport(**cached)

        total = await self.selector.get_total_count()
        active = await self.selector.get_count_by_status(EventStatus.ACTIVE)
        archived = await self.selector.get_count_by_status(EventStatus.ARCHIVED)
        daily = await self.selector.get_daily_counts(limit=7)
        monthly = await self.selector.get_monthly_counts(limit=6)
        event_types = await self.selector.get_event_type_distribution()
        sources = await self.selector.get_top_sources(limit=5)

        result = SummaryReport(
            total_events=total,
            active_events=active,
            archived_events=archived,
            daily_events=daily,
            monthly_events=monthly,
            event_type_distribution=event_types,
            active_sources=sources,
            generated_at=datetime.utcnow(),
        )
        await self.cache.set("analytics:summary", result.model_dump(), ttl=settings.CACHE_TTL_SUMMARY)
        return result

    async def get_custom_report(self, start_date: datetime, end_date: datetime) -> CustomReport:
        daily = await self.selector.get_counts_in_range(start_date, end_date)
        event_types = await self.selector.get_event_types_in_range(start_date, end_date)
        sources = await self.selector.get_sources_in_range(start_date, end_date)
        total = sum(d["count"] for d in daily)

        return CustomReport(
            start_date=start_date,
            end_date=end_date,
            total_events=total,
            event_type_distribution=event_types,
            source_distribution=sources,
            daily_breakdown=daily,
        )

    async def get_trends(self, days: int = 30) -> TrendsReport:
        data = await self.selector.get_daily_counts(limit=days)
        return TrendsReport(period=f"last_{days}_days", data=data)
