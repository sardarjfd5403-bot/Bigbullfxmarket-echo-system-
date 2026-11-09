# Development Roadmap

## Phase 0 — Foundation
- [x] Confirm product scope and platform targets
- [x] Establish architecture and safety principles
- [x] Add CI, linting, and test skeleton
- [x] Add safe configuration and risk validation foundation

## Phase 1 — Market data contracts (in progress)
- [x] Canonical sample instrument registry (Forex, gold, crypto, index)
- [x] Provider-neutral OHLCV candle model with timezone and OHLC validation
- [x] Historical and live data adapter interfaces
- [x] Batch quality checks for empty, duplicate, out-of-order, and mixed-symbol data
- [ ] Provider-specific historical and live adapters
- [ ] Instrument metadata discovery (contract size, tick size, sessions, calendars)
- [ ] Persistent historical storage and gap detection
- [ ] Economic calendar and news provider interfaces

## Phase 2 — Multi-timeframe research engine (foundation implemented)
- [x] Timeframe registry from 1s through monthly (provider availability is explicit)
- [x] EMA, RSI, ATR and realized-volatility primitives
- [x] Candlestick price-action heuristics
- [x] Basic range breakout / market-structure detection
- [x] VSA-style volume/spread analysis with volume-unit safeguards
- [x] Per-timeframe signals and combined confluence report
- [x] Initial SMC/ICT-inspired rules: liquidity sweeps, equal highs/lows, FVG, order-block candidates
- [x] Rolling VWAP context and support/resistance; [ ] session levels and multi-session context
- [ ] Fundamental/news sentiment features and economic calendar integration
- [ ] Regime classification and feature research

## Phase 3 — Backtesting and evaluation
- [ ] Event-driven backtester
- [ ] Spread, fees, swaps/funding, and slippage
- [ ] Walk-forward and out-of-sample tests
- [ ] Strategy comparison and robustness reports
- [ ] Probability calibration and uncertainty reporting

## Phase 4 — Risk and paper execution
- [ ] Independent risk service
- [ ] Position sizing and exposure constraints
- [ ] Daily loss and drawdown limits
- [ ] Kill switch and stale-data guard
- [ ] Paper broker and order reconciliation

## Phase 5 — Applications and reporting
- [ ] Web dashboard
- [ ] Desktop packaging
- [ ] Android client
- [ ] Chart annotations and screenshots
- [ ] Scheduled reports and notification adapters

## Phase 6 — Controlled live readiness
- [ ] Broker/exchange adapter security review
- [ ] Demo account validation
- [ ] Operational monitoring and recovery drills
- [ ] Explicit owner approval and per-account risk configuration
- [ ] Live mode remains opt-in and can be disabled instantly

## Performance standard
No fixed win-rate guarantee. Evaluate net expectancy, profit factor, max drawdown, tail risk, calibration, sample size, and performance across regimes. Reject strategies that only work in-sample.
