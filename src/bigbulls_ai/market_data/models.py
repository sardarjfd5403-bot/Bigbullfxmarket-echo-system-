"""Provider-neutral OHLCV candle model with strict timestamp/data validation."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    volume_type: str = "unknown"
    provider: str = "unknown"

    def __post_init__(self) -> None:
        if not self.symbol or not self.timeframe:
            raise ValueError("symbol and timeframe are required")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be the greatest OHLC value")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be the smallest OHLC value")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")
        if self.volume_type not in {"unknown", "tick", "base", "quote", "contracts"}:
            raise ValueError("unsupported volume_type")

    @property
    def timestamp_utc(self) -> datetime:
        return self.timestamp.astimezone(UTC)
