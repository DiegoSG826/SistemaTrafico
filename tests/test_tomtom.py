import asyncio
import logging

import httpx
from pydantic import SecretStr

from backend.app import tomtom


def test_live_traffic_requires_login(system):
    client, _, _ = system
    client.headers.pop("Authorization")
    assert client.get("/traffic/live").status_code == 401


def test_live_traffic_without_key_does_not_contact_provider(monkeypatch):
    async def send(*args):
        raise AssertionError("No se esperaba una solicitud a TomTom")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", send)
    snapshot = asyncio.run(tomtom.TomTomTraffic(SecretStr(""), 300).snapshot())
    assert not snapshot.configured
    assert all(segment.status == "unavailable" for segment in snapshot.segments)


def test_tomtom_shares_refresh_and_preserves_last_reading_on_partial_failure(monkeypatch, caplog):
    calls = []
    now = 100.0
    monkeypatch.setattr(tomtom, "monotonic", lambda: now)
    caplog.set_level(logging.INFO, logger="httpx")
    second_point = tomtom.QUERY_POINTS[1][1]

    async def send(_transport, request):
        assert request.url.params["key"] == "test-private-tomtom-key"
        assert request.url.params["unit"] == "kmph"
        assert request.url.host == "api.tomtom.com"
        point = request.url.params["point"]
        calls.append(point)
        if now > 100 and point == f"{second_point.latitude},{second_point.longitude}":
            return httpx.Response(429)
        return httpx.Response(200, json={"flowSegmentData": {
            "currentSpeed": 0, "freeFlowSpeed": 40, "currentTravelTime": 120,
            "freeFlowTravelTime": 60, "roadClosure": True, "confidence": 0.85,
            "coordinates": {"coordinate": [
                {"latitude": 19.425, "longitude": -99.154},
                {"latitude": 19.426, "longitude": -99.155},
            ]},
        }})

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", send)
    traffic = tomtom.TomTomTraffic(SecretStr("test-private-tomtom-key"), 300)

    async def scenario():
        nonlocal now
        first, second = await asyncio.gather(traffic.snapshot(), traffic.snapshot())
        assert first == second
        assert len(calls) == 2
        assert all(segment.status == "current" for segment in first.segments)
        assert first.segments[0].flow.speed_kmh == 0
        assert first.segments[0].flow.closed
        assert first.segments[0].retrieved_at.utcoffset().total_seconds() == 0

        now += 301
        partial = await traffic.snapshot()
        assert [segment.status for segment in partial.segments] == ["current", "stale"]
        assert partial.segments[1].flow == first.segments[1].flow
        assert partial.segments[1].retrieved_at == first.segments[1].retrieved_at
        assert await traffic.snapshot() == partial
        assert len(calls) == 4

        now += 601
        expired = await traffic.snapshot()
        assert expired.segments[1].status == "unavailable"
        assert expired.segments[1].flow is None

    asyncio.run(scenario())
    assert "test-private-tomtom-key" not in caplog.text
