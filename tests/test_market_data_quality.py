from datetime import UTC, datetime, timedelta

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.market_data.quality import validate_candle_batch


def candle(minute: int, symbol: str = "EURUSD") -> Candle:
    return Candle(symbol, "M1", datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minute),
                  1.1, 1.2, 1.0, 1.15, 100, "tick", "test-provider")


def test_valid_batch_is_accepted():
    report = validate_candle_batch([candle(0), candle(1), candle(2)], "EURUSD")
    assert report.accepted
    assert report.candle_count == 3
    assert not report.errors


def test_empty_batch_is_rejected():
    assert not validate_candle_batch([]).accepted


def test_duplicate_timestamp_is_rejected():
    report = validate_candle_batch([candle(0), candle(0)])
    assert not report.accepted
    assert any("duplicate timestamp" in error for error in report.errors)


def test_mixed_symbols_are_rejected():
    report = validate_candle_batch([candle(0), candle(1, "GBPUSD")], "EURUSD")
    assert not report.accepted


def test_out_of_order_batch_is_rejected():
    report = validate_candle_batch([candle(2), candle(1)])
    assert not report.accepted
    assert any("not chronological" in error for error in report.errors)
