from datetime import UTC, datetime, timedelta

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.research.decision import assess_confluence
from bigbulls_ai.research.models import StrategySignal
from bigbulls_ai.research.strategy_library import (
    evaluate_strategy_families, fair_value_gap, liquidity_sweep, support_resistance,
)


def candles(rows):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [Candle("BTCUSDT", "1m", start + timedelta(minutes=i), *row, 100, "base", "test")
            for i, row in enumerate(rows)]


def test_bullish_fvg_detected():
    data = candles([(10, 11, 9, 10.5), (10.5, 12, 10, 11.8), (12, 13, 11.5, 12.5)])
    assert fair_value_gap(data).direction == "bullish"


def test_liquidity_sweep_detected():
    rows = [(10, 11, 9, 10.2)] * 20 + [(10, 12, 9.5, 10.5)]
    assert liquidity_sweep(candles(rows)).direction == "bearish"


def test_support_resistance_requires_lookback():
    data = candles([(10, 11, 9, 10)] * 50)
    assert support_resistance(data) == (9, 11)


def test_all_families_evaluated_together():
    data = candles([(100+i, 101+i, 99+i, 100.8+i) for i in range(80)])
    names = {s.name for s in evaluate_strategy_families(data)}
    assert {"ema_trend", "support_resistance_context"} <= names


def test_confluence_gate_abstains_when_insufficient_families():
    one = StrategySignal("ema", "bullish", 1, .8, ("up",))
    result = assess_confluence({"1m": [one]})
    assert result.decision == "NO_TRADE"


def test_confluence_gate_accepts_candidate_only_with_broad_agreement():
    signals = [StrategySignal(f"family_{i}", "bullish", 1, .5, ("evidence",)) for i in range(4)]
    result = assess_confluence({"5m": signals})
    assert result.decision == "RESEARCH_CANDIDATE"
    assert result.direction == "bullish"
