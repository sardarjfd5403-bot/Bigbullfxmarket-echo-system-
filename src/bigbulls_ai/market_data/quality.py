"""Deterministic data-quality checks before research or trading consumes candles."""

from dataclasses import dataclass
from collections.abc import Sequence

from bigbulls_ai.market_data.models import Candle


@dataclass(frozen=True)
class DataQualityReport:
    accepted: bool
    errors: tuple[str, ...]
    candle_count: int


def validate_candle_batch(candles: Sequence[Candle], expected_symbol: str | None = None) -> DataQualityReport:
    errors: list[str] = []
    if not candles:
        return DataQualityReport(False, ("empty candle batch",), 0)

    symbol = expected_symbol.upper() if expected_symbol else candles[0].symbol.upper()
    previous_timestamp = None
    seen_timestamps = set()
    for index, candle in enumerate(candles):
        if candle.symbol.upper() != symbol:
            errors.append(f"row {index}: mixed symbol {candle.symbol}; expected {symbol}")
        timestamp = candle.timestamp_utc
        if timestamp in seen_timestamps:
            errors.append(f"row {index}: duplicate timestamp {timestamp.isoformat()}")
        if previous_timestamp is not None and timestamp < previous_timestamp:
            errors.append(f"row {index}: candles are not chronological")
        seen_timestamps.add(timestamp)
        previous_timestamp = timestamp

    return DataQualityReport(not errors, tuple(errors), len(candles))
