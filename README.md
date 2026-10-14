# Event Analytics & Reporting Platform

A production-ready backend API for ingesting, categorizing, analyzing, and archiving application events. Built with **FastAPI**, **PostgreSQL**, **Redis**, and **AWS S3**.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Features](#features)
5. [API Reference](#api-reference)
6. [Getting Started](#getting-started)
7. [Running Tests](#running-tests)
8. [Environment Variables](#environment-variables)
9. [Database Design](#database-design)
10. [Redis Design](#redis-design)
11. [AWS S3 Archival](#aws-s3-archival)
12. [Project Structure](#project-structure)

---

## Project Overview

Modern applications generate millions of events — logins, purchases, searches, errors. This platform provides a centralized backend to:

- **Ingest** events via a REST API with deduplication
- **Categorize** events (Authentication, Payments, Orders, etc.)
- **Analyze** events with daily/monthly/type/source breakdowns
- **Report** with summaries, custom date ranges, and trends
- **Archive** historical data to AWS S3 automatically

---

## Tech Stack

| Layer         | Technology                    |
|---------------|-------------------------------|
| Framework     | FastAPI 0.111 + Uvicorn       |
| Database      | PostgreSQL 16 + SQLAlchemy 2  |
| Migrations    | Alembic                       |
| Caching       | Redis 7                       |
| Cloud Storage | AWS S3 (boto3)                |
| Validation    | Pydantic v2                   |
| Testing       | Pytest + httpx + fakeredis    |
| Deployment    | Docker + Docker Compose       |

---

## Architecture

```
Request
  │
  ▼
FastAPI Router (HTTP)
  │
  ▼
Service Layer (Business Logic)
  │        │
  │        └──► Redis Cache / Dedup
  │
  ▼
Repository Layer (DB Queries)
  │
  ▼
PostgreSQL

         Archival:
Service ──► S3Client ──► AWS S3
```

**Clean Architecture layers:**

- `api/` — HTTP routing only, no business logic
- `services/` — orchestrate business rules
- `repositories/` — all DB read/write
- `selectors/` — complex SQL aggregation queries
- `integrations/` — Redis, S3 clients

---

## Features

### ✅ Event Ingestion
- `POST /api/v1/events` — Ingest events with full validation
- Returns `HTTP 201` on success, `HTTP 409` on duplicate

### ✅ Deduplication
- Redis-backed deduplication (7-day TTL)
- Prevents replay attacks and double-counting

### ✅ Event Management
- Retrieve by ID, list with filters (type, category, source, date range)
- Sorting and pagination

### ✅ Categories
- Create and manage event categories (Authentication, Payments, etc.)
- Associate events with categories

### ✅ Analytics Engine
- Daily, monthly, event-type distribution, top sources
- SQL-based aggregations — no Python loops over data
- Archived events excluded from analytics

### ✅ Reporting
- Summary report, custom date-range report, time-series trends

### ✅ Redis Caching
- Caches `daily`, `monthly`, `summary`, `top_sources`
- Configurable TTLs per cache key
- Cache invalidated on new event ingestion

### ✅ AWS S3 Archival
- Archive events older than 90 days (configurable)
- Stores JSON archives in S3 with date-partitioned keys
- Records archive metadata in the database
- Archived events excluded from analytics

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

Full interactive docs: `http://localhost:8000/docs`

### Events

| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| POST   | `/events`                   | Ingest a new event         |
| GET    | `/events`                   | List/filter events         |
| GET    | `/events/{event_id}`        | Get event by event_id      |
| POST   | `/events/archive`           | Archive old events to S3   |
| GET    | `/events/archives/list`     | List archive records       |

### Categories

| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| POST   | `/categories`               | Create a category          |
| GET    | `/categories`               | List all categories        |
| GET    | `/categories/{id}`          | Get category by ID         |

### Analytics

| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| GET    | `/analytics/daily`          | Daily event counts         |
| GET    | `/analytics/monthly`        | Monthly event counts       |
| GET    | `/analytics/event-types`    | Event type distribution    |
| GET    | `/analytics/top-sources`    | Top event sources          |

### Reports

| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| GET    | `/reports/summary`          | Full analytics summary     |
| GET    | `/reports/custom`           | Custom date-range report   |
| GET    | `/reports/trends`           | Time-series trend data     |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.12+ for local development

### Quick Start with Docker

```bash
# Clone the repo
git clone https://github.com/yourusername/event-analytics.git
cd event-analytics

# Copy environment config
cp .env.example .env

# Start all services (API + PostgreSQL + Redis)
docker compose up --build
```

The API will be available at: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit env file
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Example: Ingest an Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-20240101-001",
    "event_type": "user_login",
    "user_id": "user-42",
    "source": "web",
    "metadata": {"ip": "192.168.1.1", "browser": "Chrome"},
    "timestamp": "2024-01-01T10:00:00Z"
  }'
```

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt
pip install aiosqlite

# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## Environment Variables

| Variable                | Description                          | Default                    |
|-------------------------|--------------------------------------|----------------------------|
| `DATABASE_URL`          | PostgreSQL connection string         | `postgresql+asyncpg://...` |
| `REDIS_URL`             | Redis connection string              | `redis://localhost:6379/0` |
| `AWS_ACCESS_KEY_ID`     | AWS access key                       | —                          |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key                       | —                          |
| `AWS_REGION`            | AWS region                           | `us-east-1`                |
| `S3_BUCKET_NAME`        | S3 bucket for archives               | —                          |
| `DEBUG`                 | Enable debug logging                 | `False`                    |
| `CACHE_TTL_DAILY`       | Cache TTL for daily analytics (s)    | `300`                      |
| `CACHE_TTL_MONTHLY`     | Cache TTL for monthly analytics (s)  | `600`                      |
| `CACHE_TTL_SUMMARY`     | Cache TTL for summary report (s)     | `300`                      |
| `ARCHIVE_DAYS_THRESHOLD`| Days before events are archived      | `90`                       |

---

## Database Design

```
event_categories          events                    event_archives
─────────────────         ──────────────────────    ──────────────────
id (PK)                   id (PK, BigInt)            id (PK)
name (unique)             event_id (unique, idx)     s3_file_path
description               event_type (idx)           events_count
created_at                category_id (FK, idx)      archive_date
                          user_id                    created_at
                          source (idx)
                          metadata (JSON)
                          timestamp (idx)
                          status (idx) [ACTIVE|ARCHIVED]
                          created_at
```

**Composite indexes:**
- `(event_type, timestamp)` — analytics queries
- `(source, timestamp)` — source analytics

---

## Redis Design

### Deduplication Keys
```
dedup:event:{event_id}  →  TTL: 7 days
```
Set on ingestion. If key exists → return 409 Conflict.

### Cache Keys
```
analytics:daily        →  TTL: 5 min
analytics:monthly      →  TTL: 10 min
analytics:summary      →  TTL: 5 min
analytics:top_sources  →  TTL: 5 min
```
All invalidated on new event ingestion.

---

## AWS S3 Archival

Events older than 90 days (configurable) are archived:

1. Fetch `ACTIVE` events older than threshold
2. Serialize to JSON
3. Upload to S3: `archives/YYYY/MM/DD/events_HHMMSS.json`
4. Mark events as `ARCHIVED` in PostgreSQL
5. Store archive record (path, count, date)
6. Archived events excluded from all analytics

---

## Project Structure

```
event-analytics/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── events.py       # Event & category endpoints
│   │   │   └── analytics.py    # Analytics & report endpoints
│   │   └── router.py
│   ├── core/
│   │   ├── config.py           # Settings via pydantic-settings
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py
│   ├── db/session.py           # SQLAlchemy async engine
│   ├── models/event.py         # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── event.py            # Pydantic request/response schemas
│   │   └── analytics.py
│   ├── repositories/
│   │   └── event_repository.py # All DB operations
│   ├── selectors/
│   │   └── analytics_selector.py # SQL aggregation queries
│   ├── services/
│   │   ├── event_service.py    # Business logic + dedup
│   │   ├── analytics_service.py # Analytics + caching
│   │   └── category_service.py
│   ├── integrations/
│   │   ├── redis/client.py     # Redis cache wrapper
│   │   └── s3/client.py        # S3 upload client
│   └── main.py                 # FastAPI app + lifespan
├── tests/
│   ├── conftest.py             # Fixtures (test DB, fake redis)
│   ├── unit/                   # Unit tests (mocked dependencies)
│   └── integration/            # Integration tests (real DB+Redis)
├── alembic/
│   ├── env.py
│   └── versions/0001_initial.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Future Enhancements

- JWT authentication & API keys
- Rate limiting per user/IP
- WebSocket for real-time event streaming
- Celery task queue for async archival
- Grafana dashboard integration
- OpenTelemetry tracing
