# Phase 2 — Multi-Timeframe Research Engine

## Scope implemented in this foundation
- A timeframe registry from 1-second through monthly intervals. The engine analyzes only intervals actually supplied by a provider; it never invents missing candles.
- Dependency-free EMA, RSI, ATR and realized-volatility primitives.
- Transparent candle-pattern heuristics (engulfing, pin bars, doji).
- Basic swing-range breakout / break-of-structure detection.
- VSA-style volume/spread reading with strict checks for missing, mixed or unknown volume units.
- Per-timeframe strategy signals and a bounded confluence score, plus an overall multi-timeframe bias.
- Data-quality rejection before analysis.

## Strategy families and honest boundaries
The initial rule library covers EMA trend, RSI extremes, candlestick price action, range breakouts / market structure, and a conservative VSA heuristic. SMC/ICT concepts such as liquidity sweeps, equal highs/lows, order blocks, fair-value gaps, premium/discount and session levels should be added as individually specified, testable rules—not opaque labels. News/fundamental features require timestamped licensed/provider data and are not inferred from candles.

## Volume and timeframe caveats
Forex spot volume is commonly broker tick volume rather than centralized traded volume. Crypto venue volume and futures contract volume are not interchangeable. VSA is suppressed when units are unknown or mixed. One-second analysis requires tick/trade data; a provider that only supplies one-minute bars cannot provide genuine one-second history. Monthly bars are provider/calendar-defined and should use provider candle boundaries rather than assuming a fixed 30-day month.

## Validation before any trading use
This engine is research-only. It does not generate orders or claim predictive certainty. Next requirements: provider adapters, persistent storage and gap detection; then event-driven backtesting with spread, commissions, swaps/funding, slippage, walk-forward and out-of-sample evaluation. Live execution stays disabled by default.
