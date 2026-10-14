from datetime import date, datetime
from pydantic import BaseModel


class DailyCount(BaseModel):
    date: str
    count: int


class MonthlyCount(BaseModel):
    month: str
    count: int


class EventTypeCount(BaseModel):
    event_type: str
    count: int


class SourceCount(BaseModel):
    source: str
    count: int


class DailyAnalytics(BaseModel):
    data: list[DailyCount]
    total_days: int


class MonthlyAnalytics(BaseModel):
    data: list[MonthlyCount]
    total_months: int


class EventTypeDistribution(BaseModel):
    data: list[EventTypeCount]
    total_types: int


class TopSources(BaseModel):
    data: list[SourceCount]
    total_sources: int


class SummaryReport(BaseModel):
    total_events: int
    active_events: int
    archived_events: int
    daily_events: list[DailyCount]
    monthly_events: list[MonthlyCount]
    event_type_distribution: list[EventTypeCount]
    active_sources: list[SourceCount]
    generated_at: datetime


class CustomReport(BaseModel):
    start_date: datetime
    end_date: datetime
    total_events: int
    event_type_distribution: list[EventTypeCount]
    source_distribution: list[SourceCount]
    daily_breakdown: list[DailyCount]


class TrendPoint(BaseModel):
    date: str
    count: int


class TrendsReport(BaseModel):
    period: str
    data: list[TrendPoint]
