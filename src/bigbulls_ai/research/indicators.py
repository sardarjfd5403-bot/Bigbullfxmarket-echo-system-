"""Small dependency-free indicator primitives used for reproducible research."""

from collections.abc import Sequence
from itertools import pairwise
from math import sqrt

from bigbulls_ai.market_data.models import Candle


def ema(values: Sequence[float], period: int) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    alpha = 2.0 / (period + 1)
    result = sum(values[:period]) / period
    for value in values[period:]:
        result = alpha * value + (1.0 - alpha) * result
    return result


def rsi(values: Sequence[float], period: int = 14) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) <= period:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((period - 1) * avg_gain + gain) / period
        avg_loss = ((period - 1) * avg_loss + loss) / period
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))


def atr(candles: Sequence[Candle], period: int = 14) -> float | None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) <= period:
        return None
    ranges = []
    for previous, current in pairwise(candles):
        ranges.append(max(current.high - current.low,
                          abs(current.high - previous.close),
                          abs(current.low - previous.close)))
    value = sum(ranges[:period]) / period
    for current in ranges[period:]:
        value = ((period - 1) * value + current) / period
    return value


def realized_volatility(values: Sequence[float]) -> float | None:
    if len(values) < 3:
        return None
    returns = [values[i] / values[i - 1] - 1.0 for i in range(1, len(values))]
    mean = sum(returns) / len(returns)
    return sqrt(sum((item - mean) ** 2 for item in returns) / (len(returns) - 1))
