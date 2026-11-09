"""Transparent rule-based strategy features; not claims of guaranteed profitability."""

from collections.abc import Sequence

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.research.models import StrategySignal


def candle_pattern(candles: Sequence[Candle]) -> str:
    if len(candles) < 2:
        return "insufficient_data"
    previous, current = candles[-2:]
    body = abs(current.close - current.open)
    span = current.high - current.low
    if span <= 0:
        return "indeterminate"
    lower_wick = min(current.open, current.close) - current.low
    upper_wick = current.high - max(current.open, current.close)
    if current.close > current.open and previous.close < previous.open and current.close >= previous.open and current.open <= previous.close:
        return "bullish_engulfing"
    if current.close < current.open and previous.close > previous.open and current.open >= previous.close and current.close <= previous.open:
        return "bearish_engulfing"
    if lower_wick >= body * 2 and upper_wick <= body and current.close > current.open:
        return "bullish_pin_bar"
    if upper_wick >= body * 2 and lower_wick <= body and current.close < current.open:
        return "bearish_pin_bar"
    if body / span <= 0.1:
        return "doji"
    return "none"


def market_structure(candles: Sequence[Candle], lookback: int = 20) -> str:
    if len(candles) < 6:
        return "insufficient_data"
    window = candles[-(lookback + 1):-1]
    if not window:
        return "insufficient_data"
    last = candles[-1]
    prior_high = max(item.high for item in window)
    prior_low = min(item.low for item in window)
    if last.close > prior_high:
        return "bullish_break_of_structure"
    if last.close < prior_low:
        return "bearish_break_of_structure"
    midpoint = (prior_high + prior_low) / 2
    if last.close > midpoint:
        return "range_upper_half"
    if last.close < midpoint:
        return "range_lower_half"
    return "range_midpoint"


def vsa_read(candles: Sequence[Candle]) -> tuple[str, tuple[str, ...]]:
    if len(candles) < 21:
        return "insufficient_data", ("VSA needs at least 20 prior volume observations",)
    recent = candles[-1]
    history = candles[-21:-1]
    if recent.volume is None or any(item.volume is None for item in history):
        return "unavailable", ("Volume is missing; VSA cannot be inferred from price alone",)
    volume_kinds = {item.volume_type for item in [*history, recent]}
    if len(volume_kinds) != 1 or "unknown" in volume_kinds:
        return "unreliable", ("Volume units are mixed or unknown; compare only like-for-like volume",)
    average = sum(item.volume or 0.0 for item in history) / len(history)
    if average <= 0:
        return "unreliable", ("Baseline volume is zero",)
    ratio = (recent.volume or 0.0) / average
    spread = recent.high - recent.low
    if spread <= 0:
        return "indeterminate", ("Current candle has no range",)
    close_location = (recent.close - recent.low) / spread
    if ratio >= 1.5 and close_location >= 0.7:
        return "high_volume_demand", ()
    if ratio >= 1.5 and close_location <= 0.3:
        return "high_volume_supply", ()
    if ratio <= 0.7 and spread < sum(c.high - c.low for c in history) / len(history):
        return "low_effort_narrow_spread", ()
    return "neutral", ()


def build_signals(trend: str, structure: str, pattern: str, vsa: str, rsi_value: float | None) -> tuple[StrategySignal, ...]:
    signals: list[StrategySignal] = []
    if trend in {"bullish", "bearish"}:
        signals.append(StrategySignal("ema_trend", trend, 1.0 if trend == "bullish" else -1.0, 0.55, ("EMA 20/50 alignment",)))
    if "bullish_break" in structure or "bearish_break" in structure:
        direction = "bullish" if "bullish" in structure else "bearish"
        signals.append(StrategySignal("structure_break", direction, 1.5 if direction == "bullish" else -1.5, 0.65, (structure,)))
    if pattern in {"bullish_engulfing", "bullish_pin_bar", "bearish_engulfing", "bearish_pin_bar"}:
        direction = "bullish" if pattern.startswith("bullish") else "bearish"
        signals.append(StrategySignal("candlestick", direction, 0.75 if direction == "bullish" else -0.75, 0.5, (pattern,)))
    if vsa in {"high_volume_demand", "high_volume_supply"}:
        direction = "bullish" if vsa.endswith("demand") else "bearish"
        signals.append(StrategySignal("vsa", direction, 1.0 if direction == "bullish" else -1.0, 0.45, (vsa,), ("VSA is a heuristic and depends on trustworthy volume semantics",)))
    if rsi_value is not None and rsi_value >= 70:
        signals.append(StrategySignal("rsi_extreme", "bearish", -0.25, 0.3, ("RSI >= 70; not a standalone sell signal",)))
    elif rsi_value is not None and rsi_value <= 30:
        signals.append(StrategySignal("rsi_extreme", "bullish", 0.25, 0.3, ("RSI <= 30; not a standalone buy signal",)))
    return tuple(signals)
