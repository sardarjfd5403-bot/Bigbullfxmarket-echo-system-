# BIGBULLS AI — Production Standards and Risk Policy

## One-pass strategy evaluation
All implemented candle-derived families are evaluated together on each supplied, validated timeframe. The research library currently includes EMA trend, RSI extremes, ATR/realized volatility context, candle patterns, range structure/breakouts, VSA with volume provenance safeguards, liquidity sweeps, equal highs/lows context, fair-value gaps, order-block candidates, rolling VWAP context, and rolling support/resistance. Strategy outputs retain their evidence and caveats.

## Confluence is not certainty
The confluence gate de-duplicates strategy families across timeframes so the same correlated signal is not counted repeatedly. It requires at least four agreeing directional families, 75% agreement, and a heuristic score threshold. Otherwise it returns NO_TRADE. A RESEARCH_CANDIDATE is not an order or a promise of a profitable trade. Score and agreement are not calibrated probabilities.

## Cannot guarantee a loss probability below 1%
No market system can honestly guarantee that fewer than 1% of trades lose. A high win rate can still lose money due to occasional large losses, gaps, slippage, spread widening, funding, execution failures, and regime changes. BIGBULLS AI must not advertise 99% accuracy or suppress uncertainty. Optimize measured expectancy and tail risk instead.

## Mandatory production gates before autonomous execution
1. Historical datasets with source, timezone, volume semantics, and gap checks.
2. Event-driven backtests including realistic spread, commissions, swaps/funding, slippage, rejected orders, and latency.
3. Walk-forward and strictly out-of-sample evaluation across symbols, sessions, and market regimes.
4. Paper trading long enough to cover varied conditions; compare expected vs realized fills.
5. Independent risk controls: per-trade risk cap, daily loss cap, max drawdown, exposure/correlation cap, stale-data guard, and emergency kill switch.
6. Monitoring, audit logs, secret management, recovery tests, and manual override.
7. Live execution remains disabled by default until owner approval and release review.

## Fundamental/news inputs
News and macro analysis are intentionally not fabricated from OHLCV. Add timestamped economic calendar and news sources with event time, publication time, source, affected instruments, and licensing checks. Prevent look-ahead bias: a backtest may only use information available at that historical decision timestamp.

## Current status
This repository contains a research foundation and candidate confluence gate, not a production-validated autonomous trading system. Provider adapters, backtesting, calibrated probability models, news integrations, execution hardening, and demo validation remain release blockers.
