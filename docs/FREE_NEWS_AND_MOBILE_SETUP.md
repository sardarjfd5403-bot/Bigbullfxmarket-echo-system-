# Free news integration (no paid API key)

## Selected provider
BIGBULLS AI now includes `ShowMyTradesCalendar`, a no-key public economic-calendar adapter:
- Endpoint: https://showmytrades.com/api/public/calendar/v1
- Free, no account/API key, JSON or CSV, up to 30 days ahead.
- Currency coverage: USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF, CNY.
- Impact levels: high, medium, low, holiday.
- Fields include scheduled timestamp, currency, impact, title, forecast, previous and actual.
- Provider documentation: https://showmytrades.com/docs/api/economic-calendar

## Commercial-use boundary
The provider documentation states commercial use is allowed when the calendar is used within your own product/client offering, but the calendar itself must not be resold as a standalone calendar or exposed as a public calendar API. Review the provider's current terms before each release. Attribute the provider where practical. The provider disclaims completeness and timing guarantees. Do not package its raw calendar as a competing data feed.

## Usage
```python
from bigbulls_ai.free_calendar import ShowMyTradesCalendar

calendar = ShowMyTradesCalendar(
    currencies=("USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "CNY"),
    impacts=("high", "medium", "low"),
    days=7,
)
events = calendar.fetch_events()
for event in events:
    print(event.scheduled_at, event.currency, event.impact, event.title)
```

The adapter uses only Python's standard library and requires no API key. Network errors raise an exception; callers must fail closed and not trade on stale/missing calendar data.

## Important limitations
- This is a scheduled economic calendar, not a real-time headline/newswire feed and not an AI sentiment engine.
- A distinct publication timestamp is not supplied. The legacy `NewsEvent.published_at` field is set to the scheduled timestamp for compatibility; do not use it as a publication-time claim or for point-in-time news backtests.
- Actual/forecast values may be blank until after release. No positive/negative currency sentiment is inferred from a headline alone.
- Calendar events are a risk filter/context only. Wait for market-price confirmation, spreads and slippage checks, calibrated model validation, and all other execution gates.
- Free third-party service availability, coverage and terms can change.
- Forex Factory does not provide an official public API; do not scrape or redistribute its calendar without permission.

## Mobile-only development and demo testing
The Android MT5 app is a monitoring/trading client, not a host for the MetaTrader Python integration. Python's official MT5 integration communicates with a desktop MT5 terminal. With no Windows PC/VPS and no eligible Exness VPS:
- GitHub Actions can run automated unit tests and linting, but it is not a persistent 24/7 trading terminal.
- Run the news adapter's unit tests in CI; this verifies parsing and fail-closed behavior, not live broker execution.
- Use this system in research/paper mode only. No actual Exness demo orders can be claimed as tested from this mobile-only environment.
- Do not enable live trading or advertise it as an autonomous live-trading bot until a supported execution host, broker demo validation, monitoring, and safety controls are proven.

## Run tests
```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```
