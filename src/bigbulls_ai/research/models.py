"""Typed outputs for deterministic strategy analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySignal:
    name: str
    direction: str
    score: float
    confidence: float
    evidence: tuple[str, ...]
    caveats: tuple[str, ...] = ()


@dataclass(frozen=True)
class TimeframeAnalysis:
    timeframe: str
    candles: int
    trend: str
    ema_fast: float | None
    ema_slow: float | None
    rsi: float | None
    atr: float | None
    volatility_pct: float | None
    structure: str
    candle_pattern: str
    vsa_read: str
    signals: tuple[StrategySignal, ...]
    confluence_score: float
    data_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisReport:
    symbol: str
    analyses: tuple[TimeframeAnalysis, ...]
    overall_bias: str
    overall_score: float
    warnings: tuple[str, ...]
