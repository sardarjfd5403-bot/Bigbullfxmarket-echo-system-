# BIGBULLS AI — Autonomous Trading Intelligence Ecosystem

> Multi-asset research, risk-controlled execution, and transparent performance measurement.

## Project status
**Foundation / specification stage.** No live trading is enabled. The system must pass data validation, historical backtesting, out-of-sample evaluation, and demo trading before any real-money execution is considered.

## Confirmed product decisions
- **Markets:** Forex, crypto, gold, and supported indices.
- **Execution target:** Autonomous execution, gated by configurable risk controls and staged validation.
- **Platforms:** Desktop, Android, and web dashboard.
- **Analysis:** Technical, price action, SMC/ICT-style concepts, VSA where reliable volume data exists, macro fundamentals, scheduled economic events, and news sentiment.
- **Reporting:** Auditable trade plans, chart annotations, performance reports, and optional messaging integrations.

## Non-negotiable safety principles
1. No claim or target of guaranteed 99% accuracy. Measure real performance with out-of-sample results, costs, slippage, drawdown, and confidence calibration.
2. Paper trading is the default. Live execution remains disabled until explicit configuration and validation gates are satisfied.
3. Every order must pass pre-trade risk checks and have protective exit logic where supported.
4. Provide a global kill switch, daily loss limit, max drawdown limit, position/exposure limits, and stale-data protection.
5. Never commit broker credentials, exchange secrets, access tokens, or personal data. Use environment variables or a secrets manager.
6. Strategy/model changes require tests, versioning, and approval before production deployment.

## Repository map
- `docs/` — architecture, roadmap, security, and operating procedures
- `config/` — safe example configuration (no secrets)
- `src/` — application packages (added incrementally)
- `tests/` — automated tests
- `.github/workflows/` — CI checks

## Development sequence
1. Specification and threat model
2. Data adapters and normalized market-data contracts
3. Historical storage and data-quality checks
4. Strategy research modules
5. Backtesting with realistic fees/spread/slippage
6. Risk engine and paper-trading execution
7. Monitoring, dashboard, and reports
8. Demo validation, then carefully gated live execution

See [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), and [Security](docs/SECURITY.md).


## Free economic-calendar integration
A no-key ShowMyTrades public-calendar adapter is available in `src/bigbulls_ai/free_calendar.py`.
See [Free news and mobile setup](docs/FREE_NEWS_AND_MOBILE_SETUP.md) for usage, commercial-use boundaries, and limitations. The feed is calendar context only; it is not a real-time headline sentiment service.

**Current execution status:** research/paper mode. Android MT5 does not host the desktop Python integration. No Exness demo order execution has been validated from the mobile-only setup, and live trading is not enabled.
