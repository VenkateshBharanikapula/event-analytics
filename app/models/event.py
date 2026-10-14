import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, DateTime, Enum, ForeignKey,
    Index, Integer, JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class EventStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class EventCategory(Base):
    __tablename__ = "event_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list["Event"]] = relationship("Event", back_populates="category")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("event_categories.id"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), nullable=False, default=EventStatus.ACTIVE, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["EventCategory | None"] = relationship("EventCategory", back_populates="events")

    __table_args__ = (
        Index("ix_event_type_timestamp", "event_type", "timestamp"),
        Index("ix_source_timestamp", "source", "timestamp"),
    )


class EventArchive(Base):
    __tablename__ = "event_archives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    s3_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False)
    archive_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
