"""Provider-neutral live integration contracts.

Concrete vendor adapters are intentionally separate: supply a licensed provider,
credentials via environment/secrets manager, and a broker demo account before
connecting real endpoints. No scraping, fabricated ticks, or live orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

from bigbulls_ai.market_data.models import MarketBar, MarketTick
from bigbulls_ai.news import NewsEvent
from bigbulls_ai.risk import TradeProposal


class NewsProvider(Protocol):
    """Licensed economic-calendar/news provider."""

    def fetch_events(self, since: datetime, until: datetime) -> Sequence[NewsEvent]: ...


class TickDataProvider(Protocol):
    """Broker/exchange or licensed consolidated tick stream."""

    def latest_ticks(self, symbols: Sequence[str]) -> Sequence[MarketTick]: ...


class NewsInterpreter(Protocol):
    """Versioned, independently validated news classification model."""

    def interpret(self, event: NewsEvent) -> NewsModelOutput: ...


@dataclass(frozen=True)
class NewsModelOutput:
    event_id: str
    instrument: str
    direction: str
    probability: float
    model_version: str
    evidence: tuple[str, ...]

    def validate(self) -> None:
        if self.direction not in {"bullish", "bearish", "neutral", "unknown"}:
            raise ValueError("Invalid news model direction")
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1")
        if not self.event_id or not self.instrument or not self.model_version:
            raise ValueError("Event, instrument, and model version are required")


@dataclass(frozen=True)
class BrokerOrderResult:
    accepted: bool
    order_id: str | None
    status: str
    message: str


class DemoBroker(Protocol):
    """Demo-only broker interface; implementations must reject live accounts."""

    def submit_demo_order(self, proposal: TradeProposal, quantity: float) -> BrokerOrderResult: ...

    def account_is_demo(self) -> bool: ...


class HistoricalDataStore(Protocol):
    def bars(self, symbol: str, start: datetime, end: datetime) -> Sequence[MarketBar]: ...

    def news(self, start: datetime, end: datetime) -> Sequence[NewsEvent]: ...
