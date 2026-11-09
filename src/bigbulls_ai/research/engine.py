"""Multi-timeframe analysis engine operating only on supplied, validated candles."""

from collections.abc import Mapping, Sequence

from bigbulls_ai.market_data.models import Candle
from bigbulls_ai.market_data.quality import validate_candle_batch
from bigbulls_ai.research.indicators import atr, ema, realized_volatility, rsi
from bigbulls_ai.research.models import AnalysisReport, TimeframeAnalysis
from bigbulls_ai.research.strategies import build_signals, candle_pattern, market_structure, vsa_read
from bigbulls_ai.research.timeframes import TIMEFRAME_SECONDS


def analyze_timeframes(data: Mapping[str, Sequence[Candle]], symbol: str | None = None) -> AnalysisReport:
    """Analyze every supplied timeframe; missing provider intervals are never fabricated."""
    analyses: list[TimeframeAnalysis] = []
    warnings: list[str] = []
    symbols = {c.symbol.upper() for rows in data.values() for c in rows}
    resolved_symbol = (symbol or (next(iter(symbols)) if len(symbols) == 1 else "UNKNOWN")).upper()
    if len(symbols) > 1:
        warnings.append("Input contains multiple symbols; analysis is separated by caller responsibility")
    for timeframe, rows in sorted(data.items(), key=lambda item: TIMEFRAME_SECONDS.get(item[0].lower(), 10**12)):
        if timeframe.lower() not in TIMEFRAME_SECONDS:
            warnings.append(f"Unsupported timeframe skipped: {timeframe}")
            continue
        if not rows:
            warnings.append(f"No candles supplied for {timeframe}")
            continue
        report = validate_candle_batch(rows, expected_symbol=resolved_symbol if resolved_symbol != "UNKNOWN" else None)
        if not report.accepted:
            warnings.append(f"{timeframe} rejected: {'; '.join(report.errors)}")
            continue
        closes = [c.close for c in rows]
        fast, slow = ema(closes, 20), ema(closes, 50)
        trend = "insufficient_data"
        if fast is not None and slow is not None:
            trend = "bullish" if fast > slow else "bearish" if fast < slow else "neutral"
        rsi_value, atr_value = rsi(closes), atr(rows)
        volatility = realized_volatility(closes)
        structure = market_structure(rows)
        pattern = candle_pattern(rows)
        vsa, vsa_warnings = vsa_read(rows)
        signals = build_signals(trend, structure, pattern, vsa, rsi_value)
        score = sum(signal.score for signal in signals)
        normalized = max(-1.0, min(1.0, score / 4.0))
        local_warnings = list(vsa_warnings)
        if len(rows) < 50:
            local_warnings.append("Fewer than 50 candles: long-lookback trend context is incomplete")
        analyses.append(TimeframeAnalysis(
            timeframe=timeframe.lower(), candles=len(rows), trend=trend,
            ema_fast=fast, ema_slow=slow, rsi=rsi_value, atr=atr_value,
            volatility_pct=volatility * 100 if volatility is not None else None,
            structure=structure, candle_pattern=pattern, vsa_read=vsa,
            signals=signals, confluence_score=normalized, data_warnings=tuple(local_warnings),
        ))
    if analyses:
        total = sum(item.confluence_score for item in analyses) / len(analyses)
        bias = "bullish" if total >= 0.2 else "bearish" if total <= -0.2 else "mixed_or_neutral"
    else:
        total, bias = 0.0, "insufficient_data"
        warnings.append("No valid timeframe data available for analysis")
    return AnalysisReport(resolved_symbol, tuple(analyses), bias, total, tuple(warnings))
