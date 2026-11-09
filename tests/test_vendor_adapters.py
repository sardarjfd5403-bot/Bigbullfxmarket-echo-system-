from datetime import UTC, datetime
import json

import pytest

from bigbulls_ai.vendor_adapters import TradingEconomicsCalendar, _number


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_te_calendar_maps_documented_event_fields(monkeypatch):
    payload = [{
        "CalendarId": "123",
        "Date": "2026-11-09T12:30:00",
        "Country": "United States",
        "Event": "CPI",
        "Importance": 3,
        "Actual": "3.1%",
        "Forecast": "3.2%",
        "Previous": "3.0%",
        "SourceURL": "https://example.test/source",
    }]
    monkeypatch.setattr(
        "bigbulls_ai.vendor_adapters.urllib.request.urlopen",
        lambda request, timeout: FakeResponse(payload),
    )
    provider = TradingEconomicsCalendar("test-key")
    start = datetime(2026, 11, 9, 12, tzinfo=UTC)
    events = provider.fetch_events(start, datetime(2026, 11, 9, 13, tzinfo=UTC))
    assert len(events) == 1
    assert events[0].currency == "USD"
    assert events[0].impact == "high"
    assert events[0].actual == 3.1
    assert events[0].forecast == 3.2
    assert events[0].source == "Trading Economics"


def test_te_provider_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("TRADING_ECONOMICS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="TRADING_ECONOMICS_API_KEY"):
        TradingEconomicsCalendar("")


def test_te_provider_rejects_naive_date_range():
    provider = TradingEconomicsCalendar("test-key")
    with pytest.raises(ValueError, match="timezone-aware"):
        provider.fetch_events(datetime(2026, 11, 9), datetime(2026, 11, 10))


def test_number_parser_handles_percent_and_missing_values():
    assert _number("3.4%") == 3.4
    assert _number("") is None
    assert _number("not-released") is None
