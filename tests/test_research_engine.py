from datetime import UTC, datetime, timedelta

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.research.engine import analyze_timeframes
from bigbulls_ai.research.indicators import ema, rsi
from bigbulls_ai.research.strategies import market_structure, vsa_read
from bigbulls_ai.research.timeframes import TIMEFRAME_SECONDS, timeframe_seconds


def make_candles(count: int = 80, rising: bool = True) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    result = []
    for i in range(count):
        close = 100 + i * 0.2 if rising else 120 - i * 0.2
        result.append(Candle("EURUSD", "1m", start + timedelta(minutes=i), close - 0.05,
                             close + 0.1, close - 0.1, close, 100 + i,
                             "tick", "test"))
    return result


def test_timeframe_registry_includes_seconds_and_monthly():
    assert timeframe_seconds("1s") == 1
    assert timeframe_seconds("1mo") == 2_592_000
    assert len(TIMEFRAME_SECONDS) >= 20


def test_ema_and_rsi_are_bounded():
    assert ema([1, 2, 3, 4, 5], 3) is not None
    value = rsi(list(range(1, 20)))
    assert value == 100.0


def test_structure_detects_breakout():
    candles = make_candles(30)
    assert market_structure(candles) == "bullish_break_of_structure"


def test_vsa_refuses_unknown_volume_semantics():
    candles = make_candles(25)
    candles = [Candle(c.symbol, c.timeframe, c.timestamp, c.open, c.high, c.low,
                      c.close, c.volume, "unknown", c.provider) for c in candles]
    result, warnings = vsa_read(candles)
    assert result == "unreliable"
    assert warnings


def test_multi_timeframe_report_uses_supplied_intervals():
    one_minute = make_candles()
    report = analyze_timeframes({"1m": one_minute, "5m": [
        Candle(c.symbol, "5m", c.timestamp, c.open, c.high, c.low, c.close,
               c.volume, c.volume_type, c.provider) for c in one_minute
    ]})
    assert report.symbol == "EURUSD"
    assert [item.timeframe for item in report.analyses] == ["1m", "5m"]
    assert report.overall_bias in {"bullish", "bearish", "mixed_or_neutral"}
