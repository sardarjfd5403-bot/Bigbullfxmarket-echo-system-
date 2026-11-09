# BIGBULLS AI — Architecture

## System overview

```text
Market / Broker / Exchange / News Providers
                 |
          Data Adapters
                 |
       Validation + Normalization
                 |
      Historical Store + Live Bus
                 |
  Research Engines (technical, structure,
  price action, volume, macro, news, quant)
                 |
       Signal / Scenario Aggregator
                 |
          Risk Engine
                 |
       Paper Execution Gateway
                 |
    Broker / Exchange Gateway (later,
      disabled until release gates)
                 |
 Monitoring, audit log, dashboard, reports
```

## Core services

### 1. Data adapters
Provider-specific connectors must be isolated behind common interfaces. Each record carries provider, instrument, event time, receive time, timeframe, and quality metadata. Do not assume spot FX has a centralized consolidated volume feed; label tick volume and exchange volume distinctly.

### 2. Instrument and market registry
Maintain canonical symbols, asset class, quote/base currency, contract size, tick size, trading sessions, timezone, trading calendar, and provider symbol mapping.

### 3. Research engines
Engines produce explainable observations, not direct orders. Initial modules:
- Market structure and price action
- Technical indicators and volatility regimes
- Liquidity / SMC / ICT-inspired pattern definitions
- Volume analysis, conditional on volume provenance
- Macro calendar and fundamental context
- News event and sentiment context
- Quantitative/statistical research

Every observation includes inputs, timestamp, timeframe, rule/model version, confidence calibration metadata, and invalidation conditions.

### 4. Signal aggregation
Combine evidence without double-counting correlated indicators. Output scenarios (bullish, bearish, neutral), conditions, entry zone if justified, invalidation, and evidence. A no-trade result is valid and preferred over a forced signal.

### 5. Risk engine
Independent from strategy logic. Enforce maximum risk per trade, aggregate exposure, leverage, correlated exposure, daily loss, drawdown, order frequency, and market/data availability checks. Reject orders when inputs are stale or incomplete.

### 6. Execution gateway
Start with a simulator/paper broker. Live broker and exchange adapters are separate implementations, disabled by default, with idempotent order handling, reconciliation, audit trails, and emergency stop.

### 7. User applications
A shared authenticated API serves web, desktop, and Android clients. UI must clearly distinguish research signals, simulated positions, and live positions.

### 8. Observability
Record data lineage, decisions, model versions, rejected orders, fills, fees, slippage, and system health. Reports must show methodology and sample size.

## Quality gates
- Unit and integration tests
- Data integrity and timezone tests
- Look-ahead / survivorship-bias checks
- Walk-forward and out-of-sample evaluation
- Fees, spread, funding, and slippage modelling
- Paper-trading soak test
- Security review and explicit live-trading enablement
