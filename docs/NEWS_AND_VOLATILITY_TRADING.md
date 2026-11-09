# BIGBULLS AI — News and Volatility Trading

## Intended event-driven workflow
1. Calendar/news connectors ingest timestamped events from licensed, reliable providers. Forex Factory may be used as a human-facing reference, but automated ingestion must respect its terms and any provider API/licensing requirements. Do not assume a public scraping endpoint exists.
2. Normalize currency, instrument impact, scheduled time, publication time, actual, forecast, previous, source, and indicator direction metadata.
3. Classify the event and numeric surprise. A higher-than-forecast value is not universally positive: CPI, unemployment, rates, GDP, and employment indicators have different economic interpretations and may be regime-dependent.
4. Observe the actual market reaction: spread, depth/liquidity where available, tick/quote movement, volatility, and correlated instruments.
5. Wait for price, volume/liquidity, and multi-timeframe confirmation after release. A headline alone never triggers an order.
6. Require a calibrated out-of-sample probability estimate, acceptable spread/slippage, and risk approval.
7. The current implementation returns READY_FOR_PAPER only. It does not submit live orders.

## Volatility behavior
High volatility is not an automatic trade signal. Extreme ATR-normalized bars, abnormal spreads, poor liquidity, and slippage cause a fail-closed NO_TRADE. A future volatility strategy may trade after a shock only when the market stabilizes and a fresh setup confirms.

## Probability integrity
The 90% threshold is a configurable target gate, not a claim that the system already achieves 90% accuracy. Probability must come from a calibrated model validated on strictly out-of-sample data, with adequate sample size, calibration reports, regime breakdowns, and confidence intervals. If no valid probability exists, the gate rejects the trade.

## Production integrations still required
- Licensed real-time economic calendar/news provider adapters and health monitoring.
- Indicator-specific interpretation metadata and point-in-time news archive.
- Tick/quote/depth feed, spread/slippage estimator, and event-time synchronization.
- Backtesting with realistic release latency, revisions, spread widening, gaps, and rejected fills.
- Demo/paper execution adapter and reconciliation.
- Independent risk service and emergency kill switch.
- Explicit release approval before any live execution.

## Safety
Never hard-code a 90% score, infer market direction from a headline keyword alone, or place orders in a news spike without confirmed executable liquidity. Autonomous live execution remains disabled by default.
