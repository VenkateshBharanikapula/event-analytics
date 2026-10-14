"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", name="eventstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["category_id"], ["event_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_events_event_id", "events", ["event_id"], unique=True)
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_timestamp", "events", ["timestamp"])
    op.create_index("ix_events_source", "events", ["source"])
    op.create_index("ix_events_category_id", "events", ["category_id"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_event_type_timestamp", "events", ["event_type", "timestamp"])
    op.create_index("ix_source_timestamp", "events", ["source", "timestamp"])

    op.create_table(
        "event_archives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("s3_file_path", sa.String(length=500), nullable=False),
        sa.Column("events_count", sa.Integer(), nullable=False),
        sa.Column("archive_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("event_archives")
    op.drop_index("ix_source_timestamp", table_name="events")
    op.drop_index("ix_event_type_timestamp", table_name="events")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_category_id", table_name="events")
    op.drop_index("ix_events_source", table_name="events")
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_event_id", table_name="events")
    op.drop_table("events")
    op.drop_table("event_categories")
    sa.Enum(name="eventstatus").drop(op.get_bind())
