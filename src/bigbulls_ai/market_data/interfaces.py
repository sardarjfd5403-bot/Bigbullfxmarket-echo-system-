"""Interfaces shared by historical and live market data providers."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from bigbulls_ai.market_data.models import Candle


class HistoricalMarketData(Protocol):
    def get_candles(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> Sequence[Candle]:
        """Return candles in [start, end), ordered by timestamp."""
        ...


class LiveMarketData(Protocol):
    def subscribe(self, symbols: Sequence[str]) -> None:
        """Subscribe to provider updates. Implementations must expose data provenance."""
        ...
