"""Concrete, opt-in adapters for Trading Economics and an MT5 demo terminal.

Secrets are read from environment variables. MT5 adapter imports its optional
Windows-only package lazily and refuses non-demo accounts before order_send.
"""
 # ruff: noqa: I001
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from urllib import error, parse, request
from zoneinfo import ZoneInfo

from bigbulls_ai.integrations import BrokerOrderResult
from bigbulls_ai.market_data.models import MarketTick
from bigbulls_ai.news import NewsEvent
from bigbulls_ai.risk import TradeProposal, validate_proposal


_COUNTRY_CURRENCY = {
    "United States": "USD", "United Kingdom": "GBP", "Euro Area": "EUR",
    "Germany": "EUR", "France": "EUR", "Italy": "EUR", "Spain": "EUR",
    "Japan": "JPY", "Australia": "AUD", "New Zealand": "NZD",
    "Canada": "CAD", "Switzerland": "CHF", "China": "CNY",
}


def _number(value: object) -> float | None:
    if value is None or value == "":
        return None
    cleaned = str(value).replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


class TradingEconomicsCalendar:
    """Read the documented TE economic-calendar endpoint using an API key."""

    def __init__(self, api_key: str | None = None, naive_timezone: str | None = None) -> None:
        self.api_key = api_key or os.getenv("TRADING_ECONOMICS_API_KEY", "")
        if not self.api_key:
            raise ValueError("Set TRADING_ECONOMICS_API_KEY; never commit API keys")
        self.timezone = ZoneInfo(naive_timezone or os.getenv("TRADING_ECONOMICS_NAIVE_TIMEZONE", "UTC"))

    def fetch_events(self, since: datetime, until: datetime) -> list[NewsEvent]:
        if not isinstance(since, datetime) or not isinstance(until, datetime):
            raise TypeError("since and until must be datetime values")
        if since.tzinfo is None or until.tzinfo is None or until < since:
            raise ValueError("since/until must be ordered timezone-aware timestamps")
        start = since.astimezone(UTC).date().isoformat()
        end = until.astimezone(UTC).date().isoformat()
        query = parse.urlencode({"f": "json"})
        url = (
            "https://api.tradingeconomics.com/calendar/country/All/"
            f"{start}/{end}?{query}"
        )
        http_request = request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": self.api_key,
                "User-Agent": "BIGBULLS-AI/0.1",
            },
        )
        try:
            with request.urlopen(http_request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Trading Economics calendar request failed") from exc
        if not isinstance(payload, list):
            raise TypeError("Unexpected Trading Economics calendar response")
        events: list[NewsEvent] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            date_text = item.get("Date")
            event_id = str(item.get("CalendarId") or "")
            if not date_text or not event_id:
                continue
            release_time = datetime.fromisoformat(str(date_text))
            if release_time.tzinfo is None:
                release_time = release_time.replace(tzinfo=self.timezone)
            release_time = release_time.astimezone(UTC)
            if not since.astimezone(UTC) <= release_time <= until.astimezone(UTC):
                continue
            importance = int(item.get("Importance") or 0)
            impact = {1: "low", 2: "medium", 3: "high"}.get(importance, "unknown")
            country = str(item.get("Country") or "")
            currency = str(item.get("Currency") or _COUNTRY_CURRENCY.get(country, ""))
            if not currency:
                currency = "UNKNOWN"
            title = str(item.get("Event") or item.get("Category") or "Economic event")
            events.append(
                NewsEvent(
                    event_id=event_id,
                    title=title,
                    currency=currency,
                    scheduled_at=release_time,
                    # Calendar Date is the scheduled release timestamp. Actual/forecast
                    # values are populated only after release; no headline-only signal.
                    published_at=release_time,
                    impact=impact,
                    actual=_number(item.get("Actual")),
                    forecast=_number(item.get("Forecast")) or _number(item.get("TEForecast")),
                    previous=_number(item.get("Previous")),
                    source="Trading Economics",
                    source_url=str(item.get("SourceURL") or "") or None,
                )
            )
        return events


class MT5DemoAdapter:
    """MT5 terminal adapter. Requires an installed, logged-in MT5 terminal on Windows."""

    def __init__(self, terminal_path: str | None = None) -> None:
        self.terminal_path = terminal_path or os.getenv("MT5_TERMINAL_PATH")
        self._mt5 = None

    def connect(self) -> None:
        if os.name != "nt":
            raise RuntimeError("MetaTrader5 Python integration requires Windows")
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError("Install the optional MetaTrader5 package on Windows") from exc
        initialized = mt5.initialize(self.terminal_path) if self.terminal_path else mt5.initialize()
        if not initialized:
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        self._mt5 = mt5
        if not self.account_is_demo():
            mt5.shutdown()
            self._mt5 = None
            raise RuntimeError("Connected MT5 account is not DEMO; adapter halted")

    def close(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()
            self._mt5 = None

    def account_is_demo(self) -> bool:
        if self._mt5 is None:
            return False
        account = self._mt5.account_info()
        return bool(
            account is not None
            and account.trade_mode == self._mt5.ACCOUNT_TRADE_MODE_DEMO
        )

    def latest_ticks(self, symbols: list[str] | tuple[str, ...]) -> list[MarketTick]:
        if not self.account_is_demo():
            raise RuntimeError("No verified MT5 demo session")
        ticks: list[MarketTick] = []
        for symbol in symbols:
            if not self._mt5.symbol_select(symbol, True):
                continue
            tick = self._mt5.symbol_info_tick(symbol)
            if tick is None or tick.bid <= 0 or tick.ask < tick.bid:
                continue
            ticks.append(
                MarketTick(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(tick.time, tz=UTC),
                    bid=float(tick.bid),
                    ask=float(tick.ask),
                    provider="MT5-Exness-Demo",
                )
            )
        return ticks

    def submit_demo_order(self, proposal: TradeProposal, quantity: float) -> BrokerOrderResult:
        if not self.account_is_demo():
            return BrokerOrderResult(False, None, "halted", "No verified MT5 demo account")
        validate_proposal(proposal)
        if quantity <= 0:
            return BrokerOrderResult(False, None, "rejected", "Quantity must be positive")
        symbol_info = self._mt5.symbol_info(proposal.symbol)
        tick = self._mt5.symbol_info_tick(proposal.symbol)
        if symbol_info is None or tick is None:
            return BrokerOrderResult(False, None, "rejected", "Symbol/tick unavailable")
        side_buy = proposal.side == "buy"
        order_type = self._mt5.ORDER_TYPE_BUY if side_buy else self._mt5.ORDER_TYPE_SELL
        price = float(tick.ask if side_buy else tick.bid)
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": proposal.symbol,
            "volume": float(quantity),
            "type": order_type,
            "price": price,
            "sl": float(proposal.stop_loss),
            "tp": float(proposal.take_profit),
            "deviation": 10,
            "magic": 8112026,
            "comment": "BIGBULLS-AI-DEMO",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": symbol_info.filling_mode,
        }
        checked = self._mt5.order_check(request)
        if checked is None or checked.retcode != 0:
            return BrokerOrderResult(
                False, None, "rejected", f"MT5 order_check failed: {self._mt5.last_error()}"
            )
        result = self._mt5.order_send(request)
        if result is None or result.retcode != self._mt5.TRADE_RETCODE_DONE:
            return BrokerOrderResult(
                False, None, "rejected", f"MT5 demo order rejected: {self._mt5.last_error()}"
            )
        return BrokerOrderResult(True, str(result.order), "accepted", "MT5 demo order accepted")
