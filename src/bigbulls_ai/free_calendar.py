"""Free, no-key economic calendar adapter.

Uses the public ShowMyTrades calendar endpoint. This is a calendar/news-risk
feed, not a licensed real-time headline sentiment service. Fail closed on
malformed or unavailable responses.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from urllib import error, parse, request

from bigbulls_ai.news import NewsEvent


class ShowMyTradesCalendar:
    """Fetch scheduled macro events from the provider's free public JSON API."""

    ENDPOINT = "https://showmytrades.com/api/public/calendar/v1"

    def __init__(
        self,
        currencies: tuple[str, ...] = ("USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY"),
        impacts: tuple[str, ...] = ("high", "medium", "low"),
        days: int = 7,
        timeout: float = 15.0,
    ) -> None:
        if not 1 <= days <= 30:
            raise ValueError("days must be between 1 and 30")
        allowed_currencies = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY"}
        allowed_impacts = {"high", "medium", "low", "holiday"}
        if not currencies or any(c.upper() not in allowed_currencies for c in currencies):
            raise ValueError("Unsupported or empty currency selection")
        if not impacts or any(i.lower() not in allowed_impacts for i in impacts):
            raise ValueError("Unsupported or empty impact selection")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.currencies = tuple(c.upper() for c in currencies)
        self.impacts = tuple(i.lower() for i in impacts)
        self.days = days
        self.timeout = timeout

    def fetch_events(
        self, since: datetime | None = None, until: datetime | None = None
    ) -> list[NewsEvent]:
        now = datetime.now(UTC)
        start = since or (now - timedelta(hours=6))
        end = until or (now + timedelta(days=self.days))
        if start.tzinfo is None or end.tzinfo is None or end < start:
            raise ValueError("since/until must be ordered timezone-aware timestamps")
        params = parse.urlencode({
            "currency": ",".join(self.currencies),
            "impact": ",".join(self.impacts),
            "days": str(self.days),
            "format": "json",
        })
        req = request.Request(
            f"{self.ENDPOINT}?{params}",
            headers={"Accept": "application/json", "User-Agent": "BIGBULLS-AI/0.1"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Free economic calendar request failed") from exc

        if isinstance(payload, dict):
            rows = payload.get("events", payload.get("data"))
        else:
            rows = payload
        if not isinstance(rows, list):
            raise TypeError("Unexpected free calendar response: expected event list")

        events: list[NewsEvent] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw_ts = row.get("ts")
            raw_time = row.get("time")
            try:
                if raw_ts is not None:
                    scheduled = datetime.fromtimestamp(float(raw_ts), tz=UTC)
                elif raw_time:
                    scheduled = datetime.fromisoformat(str(raw_time))
                    if scheduled.tzinfo is None:
                        continue
                    scheduled = scheduled.astimezone(UTC)
                else:
                    continue
            except (TypeError, ValueError, OverflowError, OSError):
                continue
            if not start.astimezone(UTC) <= scheduled <= end.astimezone(UTC):
                continue

            event_id = str(row.get("id") or row.get("event_id") or "")
            title = str(row.get("title") or "").strip()
            currency = str(row.get("currency") or "").upper()
            impact = str(row.get("impact") or "unknown").lower()
            if not event_id or not title or currency not in self.currencies:
                continue
            if impact not in {"low", "medium", "high"}:
                impact = "unknown"

            def number(value: object) -> float | None:
                if value is None or value == "":
                    return None
                try:
                    return float(str(value).replace(",", "").replace("%", "").strip())
                except ValueError:
                    return None

            # The API does not provide a distinct publication timestamp. Keep
            # scheduled_at in this legacy field; do not treat it as release time
            # for point-in-time backtests.
            events.append(NewsEvent(
                event_id=event_id,
                title=title,
                currency=currency,
                scheduled_at=scheduled,
                published_at=scheduled,
                impact=impact,
                actual=number(row.get("actual")),
                forecast=number(row.get("forecast")),
                previous=number(row.get("previous")),
                source="ShowMyTrades public economic calendar",
                source_url="https://showmytrades.com/tools/economic-calendar",
            ))
        return events
