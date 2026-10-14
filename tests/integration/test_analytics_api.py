from datetime import datetime, timezone

import pytest

BASE = "/api/v1"


# ── Categories ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_category(client):
    resp = await client.post(
        f"{BASE}/categories",
        json={"name": "Authentication", "description": "Auth events"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Authentication"


@pytest.mark.asyncio
async def test_list_categories(client):
    await client.post(f"{BASE}/categories", json={"name": "Payments"})
    resp = await client.get(f"{BASE}/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_category_not_found(client):
    resp = await client.get(f"{BASE}/categories/999")
    assert resp.status_code == 404


# ── Analytics ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_daily_analytics(client):
    resp = await client.get(f"{BASE}/analytics/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total_days" in data


@pytest.mark.asyncio
async def test_monthly_analytics(client):
    resp = await client.get(f"{BASE}/analytics/monthly")
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_event_type_distribution(client):
    resp = await client.get(f"{BASE}/analytics/event-types")
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_top_sources(client):
    resp = await client.get(f"{BASE}/analytics/top-sources")
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_summary_report(client):
    resp = await client.get(f"{BASE}/reports/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "active_events" in data
    assert "event_type_distribution" in data


@pytest.mark.asyncio
async def test_custom_report(client):
    resp = await client.get(
        f"{BASE}/reports/custom",
        params={
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "daily_breakdown" in data


@pytest.mark.asyncio
async def test_trends_report(client):
    resp = await client.get(f"{BASE}/reports/trends?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "period" in data
    assert data["period"] == "last_7_days"
