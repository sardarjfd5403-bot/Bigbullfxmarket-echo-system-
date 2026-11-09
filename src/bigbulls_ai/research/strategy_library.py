"""Expanded, transparent strategy-family feature library.

These are rule-based observations, not standalone trading recommendations. Every
family runs on the same validated candle history and reports unavailable inputs.
"""
from collections.abc import Sequence
from statistics import mean

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.research.models import StrategySignal


def _signal(name: str, direction: str, weight: float, evidence: str, caveat: str = "") -> StrategySignal:
    return StrategySignal(name, direction, weight if direction == "bullish" else -weight,
                          0.4, (evidence,), (caveat,) if caveat else ())


def liquidity_sweep(candles: Sequence[Candle], lookback: int = 20) -> StrategySignal | None:
    if len(candles) < lookback + 1:
        return None
    prior = candles[-lookback-1:-1]
    last = candles[-1]
    high, low = max(c.high for c in prior), min(c.low for c in prior)
    if last.high > high and last.close < high:
        return _signal("liquidity_sweep", "bearish", 0.8, "Wicked above prior range high and closed back below")
    if last.low < low and last.close > low:
        return _signal("liquidity_sweep", "bullish", 0.8, "Wicked below prior range low and closed back above")
    return None


def fair_value_gap(candles: Sequence[Candle]) -> StrategySignal | None:
    if len(candles) < 3:
        return None
    a, _, c = candles[-3:]
    if c.low > a.high:
        return _signal("fair_value_gap", "bullish", 0.5, f"Three-candle bullish gap: {a.high:.8g}–{c.low:.8g}")
    if c.high < a.low:
        return _signal("fair_value_gap", "bearish", 0.5, f"Three-candle bearish gap: {c.high:.8g}–{a.low:.8g}")
    return None


def equal_highs_lows(candles: Sequence[Candle], tolerance_pct: float = 0.0005) -> tuple[str, ...]:
    if len(candles) < 10:
        return ()
    window = candles[-30:]
    highs = [c.high for c in window]
    lows = [c.low for c in window]
    max_high = max(highs)
    min_low = min(lows)
    equal_high = sum(abs(x - max_high) / max_high <= tolerance_pct for x in highs) >= 2
    equal_low = sum(abs(x - min_low) / min_low <= tolerance_pct for x in lows) >= 2
    found = []
    if equal_high:
        found.append("equal_highs_liquidity_pool")
    if equal_low:
        found.append("equal_lows_liquidity_pool")
    return tuple(found)


def order_block_candidate(candles: Sequence[Candle]) -> StrategySignal | None:
    """Conservative last-opposite-candle candidate before a strong displacement."""
    if len(candles) < 6:
        return None
    prior, displacement = candles[-2], candles[-1]
    avg_range = mean(c.high - c.low for c in candles[-6:-1])
    move = abs(displacement.close - displacement.open)
    if avg_range <= 0 or move < 1.5 * avg_range:
        return None
    if prior.close < prior.open and displacement.close > displacement.open:
        return _signal("order_block_candidate", "bullish", 0.4, "Last bearish candle before bullish displacement")
    if prior.close > prior.open and displacement.close < displacement.open:
        return _signal("order_block_candidate", "bearish", 0.4, "Last bullish candle before bearish displacement")
    return None


def vwap_deviation(candles: Sequence[Candle], lookback: int = 20) -> StrategySignal | None:
    window = candles[-lookback:]
    if len(window) < lookback or any(c.volume is None for c in window):
        return None
    kinds = {c.volume_type for c in window}
    if len(kinds) != 1 or "unknown" in kinds:
        return None
    total_volume = sum(c.volume or 0.0 for c in window)
    if total_volume <= 0:
        return None
    vwap = sum(((c.high + c.low + c.close) / 3) * (c.volume or 0.0) for c in window) / total_volume
    last = candles[-1].close
    if last > vwap and window[-1].close > window[-1].open:
        return _signal("vwap_context", "bullish", 0.3, "Price above rolling VWAP with positive latest candle")
    if last < vwap and window[-1].close < window[-1].open:
        return _signal("vwap_context", "bearish", 0.3, "Price below rolling VWAP with negative latest candle")
    return None


def support_resistance(candles: Sequence[Candle], lookback: int = 50) -> tuple[float, float] | None:
    if len(candles) < lookback:
        return None
    window = candles[-lookback:]
    return min(c.low for c in window), max(c.high for c in window)


def evaluate_strategy_families(candles: Sequence[Candle]) -> tuple[StrategySignal, ...]:
    """Evaluate every enabled candle-derived family in one pass."""
    from bigbulls_ai.research.indicators import ema, rsi
    from bigbulls_ai.research.strategies import (
        build_signals,
        candle_pattern,
        market_structure,
        vsa_read,
    )

    closes = [c.close for c in candles]
    fast, slow = ema(closes, 20), ema(closes, 50)
    trend = "insufficient_data" if fast is None or slow is None else ("bullish" if fast > slow else "bearish" if fast < slow else "neutral")
    vsa, _ = vsa_read(candles)
    signals = list(build_signals(trend, market_structure(candles), candle_pattern(candles), vsa, rsi(closes)))
    for candidate in (liquidity_sweep(candles), fair_value_gap(candles), order_block_candidate(candles), vwap_deviation(candles)):
        if candidate is not None:
            signals.append(candidate)
    for observation in equal_highs_lows(candles):
        signals.append(StrategySignal(observation, "neutral", 0.0, 0.25, (observation,), ("Liquidity pool is context, not a directional entry by itself",)))
    levels = support_resistance(candles)
    if levels:
        signals.append(StrategySignal("support_resistance_context", "neutral", 0.0, 0.2,
                                      (f"rolling support={levels[0]:.8g}, resistance={levels[1]:.8g}",)))
    return tuple(signals)
