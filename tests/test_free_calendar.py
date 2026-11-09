import json
from datetime import UTC, datetime, timedelta

import pytest

from bigbulls_ai.free_calendar import ShowMyTradesCalendar


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_free_calendar_maps_json_events(monkeypatch):
    scheduled = datetime.now(UTC) + timedelta(hours=1)
    payload = {"events": [{
        "id": "evt-1",
        "ts": scheduled.timestamp(),
        "currency": "USD",
        "impact": "high",
        "title": "US CPI",
        "actual": "3.1",
        "forecast": "3.0",
        "previous": "2.9",
    }]}
    monkeypatch.setattr(
        "bigbulls_ai.free_calendar.request.urlopen",
        lambda req, timeout: FakeResponse(payload),
    )
    provider = ShowMyTradesCalendar()
    events = provider.fetch_events(
        datetime.now(UTC), datetime.now(UTC) + timedelta(days=2)
    )
    assert len(events) == 1
    assert events[0].event_id == "evt-1"
    assert events[0].currency == "USD"
    assert events[0].impact == "high"
    assert events[0].actual == 3.1
    assert events[0].forecast == 3.0


def test_free_calendar_rejects_bad_date_range():
    provider = ShowMyTradesCalendar()
    with pytest.raises(ValueError, match="timezone-aware"):
        provider.fetch_events(datetime(2026, 1, 1), datetime(2026, 1, 2))


def test_free_calendar_rejects_unsupported_configuration():
    with pytest.raises(ValueError):
        ShowMyTradesCalendar(currencies=("BTC",))
    with pytest.raises(ValueError):
        ShowMyTradesCalendar(days=31)


def test_free_calendar_skips_unusable_rows(monkeypatch):
    monkeypatch.setattr(
        "bigbulls_ai.free_calendar.request.urlopen",
        lambda req, timeout: FakeResponse({"events": [{"title": "bad row"}]}),
    )
    events = ShowMyTradesCalendar().fetch_events(
        datetime.now(UTC) - timedelta(days=1),
        datetime.now(UTC) + timedelta(days=2),
    )
    assert events == []
