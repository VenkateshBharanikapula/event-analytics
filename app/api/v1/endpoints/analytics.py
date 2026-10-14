from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.redis.client import RedisCache, get_redis
from app.schemas.analytics import (
    CustomReport,
    DailyAnalytics,
    EventTypeDistribution,
    MonthlyAnalytics,
    SummaryReport,
    TopSources,
    TrendsReport,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def get_analytics_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AnalyticsService:
    return AnalyticsService(db, RedisCache(redis))


@router.get(
    "/analytics/daily",
    response_model=DailyAnalytics,
    summary="Daily event counts (last 30 days)",
    tags=["Analytics"],
)
async def get_daily_analytics(svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_daily()


@router.get(
    "/analytics/monthly",
    response_model=MonthlyAnalytics,
    summary="Monthly event counts (last 12 months)",
    tags=["Analytics"],
)
async def get_monthly_analytics(svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_monthly()


@router.get(
    "/analytics/event-types",
    response_model=EventTypeDistribution,
    summary="Distribution of event types",
    tags=["Analytics"],
)
async def get_event_type_distribution(svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_event_types()


@router.get(
    "/analytics/top-sources",
    response_model=TopSources,
    summary="Top event sources",
    tags=["Analytics"],
)
async def get_top_sources(svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_top_sources()


@router.get(
    "/reports/summary",
    response_model=SummaryReport,
    summary="Full analytics summary report",
    tags=["Reports"],
)
async def get_summary_report(svc: AnalyticsService = Depends(get_analytics_service)):
    return await svc.get_summary()


@router.get(
    "/reports/custom",
    response_model=CustomReport,
    summary="Custom date-range report",
    tags=["Reports"],
)
async def get_custom_report(
    start_date: datetime = Query(..., description="Report start date (ISO 8601)"),
    end_date: datetime = Query(..., description="Report end date (ISO 8601)"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_custom_report(start_date, end_date)


@router.get(
    "/reports/trends",
    response_model=TrendsReport,
    summary="Time-series trend data for dashboards",
    tags=["Reports"],
)
async def get_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to include"),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    return await svc.get_trends(days)
