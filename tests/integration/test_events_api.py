from datetime import datetime, timezone

import pytest


BASE = "/api/v1"


def event_payload(event_id: str = "evt-001", **kwargs):
    return {
        "event_id": event_id,
        "event_type": "user_login",
        "user_id": "user-1",
        "source": "web",
        "metadata": {"ip": "127.0.0.1"},
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        **kwargs,
    }


@pytest.mark.asyncio
async def test_create_event_returns_201(client):
    resp = await client.post(f"{BASE}/events", json=event_payload("evt-int-001"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_id"] == "evt-int-001"
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_create_duplicate_event_returns_409(client):
    payload = event_payload("evt-dup-001")
    await client.post(f"{BASE}/events", json=payload)
    resp = await client.post(f"{BASE}/events", json=payload)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_event_by_id(client):
    payload = event_payload("evt-get-001")
    await client.post(f"{BASE}/events", json=payload)

    resp = await client.get(f"{BASE}/events/evt-get-001")
    assert resp.status_code == 200
    assert resp.json()["event_id"] == "evt-get-001"


@pytest.mark.asyncio
async def test_get_nonexistent_event_returns_404(client):
    resp = await client.get(f"{BASE}/events/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_events_returns_paginated_response(client):
    for i in range(3):
        await client.post(f"{BASE}/events", json=event_payload(f"evt-list-{i}"))

    resp = await client.get(f"{BASE}/events?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_events_filter_by_source(client):
    await client.post(
        f"{BASE}/events",
        json=event_payload("evt-src-001", source="mobile"),
    )
    resp = await client.get(f"{BASE}/events?source=mobile")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["source"] == "mobile" for item in data["items"])


@pytest.mark.asyncio
async def test_list_events_filter_by_event_type(client):
    await client.post(
        f"{BASE}/events",
        json=event_payload("evt-type-001", event_type="purchase"),
    )
    resp = await client.get(f"{BASE}/events?event_type=purchase")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["event_type"] == "purchase" for item in data["items"])


@pytest.mark.asyncio
async def test_create_event_missing_field_returns_422(client):
    resp = await client.post(
        f"{BASE}/events",
        json={"event_id": "evt-bad-001"},  # missing required fields
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
