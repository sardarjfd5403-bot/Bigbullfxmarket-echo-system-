# Development Roadmap

## Phase 0 — Foundation (current)
- [x] Confirm product scope and platform targets
- [x] Establish architecture and safety principles
- [ ] Add CI, linting, type checks, and test skeleton
- [ ] Add configuration schema and local developer guide

## Phase 1 — Market data
- [ ] Instrument registry and canonical symbols
- [ ] Provider adapter interfaces
- [ ] Historical OHLCV ingestion
- [ ] Live quote ingestion
- [ ] Data validation, gap detection, and provenance
- [ ] Economic calendar/news provider interfaces

## Phase 2 — Research and strategy library
- [ ] Technical indicators and volatility regimes
- [ ] Price action and market structure
- [ ] Explicitly defined SMC/ICT-inspired rules
- [ ] Volume analysis with source-aware semantics
- [ ] Macro/news context
- [ ] Quantitative feature research

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
