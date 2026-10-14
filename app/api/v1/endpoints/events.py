from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEventException, EventNotFoundException
from app.db.session import get_db
from app.integrations.redis.client import RedisCache, get_redis
from app.integrations.s3.client import s3_client
from app.schemas.event import (
    ArchiveRead,
    ArchiveResponse,
    CategoryCreate,
    CategoryRead,
    EventCreate,
    EventListParams,
    EventRead,
    PaginatedEvents,
)
from app.services.category_service import CategoryService
from app.services.event_service import EventService

router = APIRouter()


def get_event_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> EventService:
    return EventService(db, RedisCache(redis))


def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(db)


# ── Event Ingestion ──────────────────────────────────────────────────────────

@router.post(
    "/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new event",
    tags=["Events"],
)
async def create_event(
    payload: EventCreate,
    svc: EventService = Depends(get_event_service),
):
    """Receive and store a new event. Returns 409 if event_id already exists."""
    try:
        return await svc.ingest_event(payload)
    except DuplicateEventException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── Event Retrieval ──────────────────────────────────────────────────────────

@router.get(
    "/events/{event_id}",
    response_model=EventRead,
    summary="Get event by event_id",
    tags=["Events"],
)
async def get_event(
    event_id: str,
    svc: EventService = Depends(get_event_service),
):
    try:
        return await svc.get_event(event_id)
    except EventNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/events",
    response_model=PaginatedEvents,
    summary="List and filter events",
    tags=["Events"],
)
async def list_events(
    event_type: str | None = Query(None, description="Filter by event type"),
    category_id: int | None = Query(None, description="Filter by category"),
    source: str | None = Query(None, description="Filter by source"),
    start_date: str | None = Query(None, description="Filter from date (ISO 8601)"),
    end_date: str | None = Query(None, description="Filter to date (ISO 8601)"),
    sort_by: str = Query("timestamp", description="Field to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: EventService = Depends(get_event_service),
):
    from datetime import datetime

    params = EventListParams(
        event_type=event_type,
        category_id=category_id,
        source=source,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return await svc.list_events(params)


# ── Archive ──────────────────────────────────────────────────────────────────

@router.post(
    "/events/archive",
    response_model=ArchiveResponse,
    summary="Archive events older than configured threshold",
    tags=["Archive"],
)
async def archive_events(svc: EventService = Depends(get_event_service)):
    return await svc.archive_old_events(s3_client)


@router.get(
    "/events/archives/list",
    response_model=list[ArchiveRead],
    summary="List all archive records",
    tags=["Archive"],
)
async def list_archives(svc: EventService = Depends(get_event_service)):
    return await svc.get_archives()


# ── Categories ───────────────────────────────────────────────────────────────

@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event category",
    tags=["Categories"],
)
async def create_category(
    payload: CategoryCreate,
    svc: CategoryService = Depends(get_category_service),
):
    return await svc.create_category(payload)


@router.get(
    "/categories",
    response_model=list[CategoryRead],
    summary="List all categories",
    tags=["Categories"],
)
async def list_categories(svc: CategoryService = Depends(get_category_service)):
    return await svc.list_categories()


@router.get(
    "/categories/{category_id}",
    response_model=CategoryRead,
    summary="Get category by ID",
    tags=["Categories"],
)
async def get_category(
    category_id: int,
    svc: CategoryService = Depends(get_category_service),
):
    from app.core.exceptions import CategoryNotFoundException
    try:
        return await svc.get_category(category_id)
    except CategoryNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
