from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.event import EventStatus


# ── Category Schemas ─────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Event Schemas ─────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=255, description="Unique event identifier")
    event_type: str = Field(..., min_length=1, max_length=100, description="Type of event")
    user_id: str = Field(..., min_length=1, max_length=255, description="User who triggered the event")
    source: str = Field(..., min_length=1, max_length=255, description="Source system or service")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional event metadata")
    timestamp: datetime = Field(..., description="When the event occurred")
    category_id: int | None = Field(default=None, description="Category ID (optional)")

    @field_validator("event_type")
    @classmethod
    def event_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_type must not be blank")
        return v.strip()


class EventRead(BaseModel):
    id: int
    event_id: str
    event_type: str
    user_id: str
    source: str
    metadata: dict[str, Any] | None = Field(alias="metadata_")
    timestamp: datetime
    status: EventStatus
    created_at: datetime
    category: CategoryRead | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class EventListParams(BaseModel):
    event_type: str | None = None
    category_id: int | None = None
    source: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedEvents(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EventRead]


# ── Archive Schemas ───────────────────────────────────────────────────────────

class ArchiveRead(BaseModel):
    id: int
    s3_file_path: str
    events_count: int
    archive_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ArchiveResponse(BaseModel):
    message: str
    archived_count: int
    s3_path: str
