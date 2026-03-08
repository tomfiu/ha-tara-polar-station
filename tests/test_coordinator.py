"""Coordinator and API mock tests."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("homeassistant")

from custom_components.tara_polar_station.const import EVENT_POSITION_UPDATED
from custom_components.tara_polar_station.coordinator import (
    TaraPolarStationCoordinator,
    TaraTelemetryApiClient,
)


class _FakeBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any] | None]] = []

    def async_fire(self, event_type: str, event_data: dict[str, Any] | None = None) -> None:
        self.events.append((event_type, event_data))


class _FakeResponse:
    def __init__(self, payload: Mapping[str, Any], status: int = 200) -> None:
        self._payload = payload
        self.status = status

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self, content_type: str | None = None) -> Mapping[str, Any]:
        return self._payload


class _FakeSession:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = payload

    def get(self, _url: str, timeout: int) -> _FakeResponse:
        del timeout
        return _FakeResponse(self._payload)


@pytest.mark.asyncio
async def test_api_client_parses_mock_payload() -> None:
    """API client should normalize common payload fields."""
    session = _FakeSession(
        {
            "data": {
                "lat": 79.332,
                "lon": -23.992,
                "speed": 0.3,
                "course": 40,
                "timestamp": "2026-03-08T12:30:00Z",
            }
        }
    )
    client = TaraTelemetryApiClient(session)  # type: ignore[arg-type]

    telemetry = await client.async_fetch_telemetry()

    assert telemetry["latitude"] == 79.332
    assert telemetry["longitude"] == -23.992
    assert telemetry["speed"] == 0.3
    assert telemetry["course"] == 40


@pytest.mark.asyncio
async def test_coordinator_builds_state_and_fires_position_event(monkeypatch: pytest.MonkeyPatch) -> None:
    """Coordinator should enrich telemetry and fire update event."""
    hass = SimpleNamespace(
        loop=asyncio.get_running_loop(),
        config=SimpleNamespace(latitude=50.0755, longitude=14.4378),
        bus=_FakeBus(),
    )
    entry = SimpleNamespace(options={}, entry_id="entry_1")
    session = _FakeSession({})

    coordinator = TaraPolarStationCoordinator(hass, entry, session)  # type: ignore[arg-type]

    async def _mock_fetch() -> dict[str, Any]:
        return {
            "latitude": 79.332,
            "longitude": -23.992,
            "speed": 0.3,
            "course": 40.0,
            "timestamp": datetime(2026, 3, 8, 12, 30, tzinfo=timezone.utc),
            "source": "mock",
        }

    monkeypatch.setattr(coordinator._client, "async_fetch_telemetry", _mock_fetch)
    state = await coordinator._async_update_data()
    coordinator.data = state

    assert state["mission_phase"] == "drift"
    assert state["in_arctic_circle"] is True
    assert state["distance_to_north_pole"] >= 0
    assert any(event_type == EVENT_POSITION_UPDATED for event_type, _ in hass.bus.events)
