# BIGBULLS AI integration status

## Implemented in repository
- Provider-neutral contracts for licensed economic news, tick feeds, historical stores, model interpretation, and demo brokers.
- Structured macro-surprise interpreter. It deliberately returns `unknown` when indicator semantics are missing; it is not a general LLM headline classifier.
- Point-in-time news event-study harness with entry delay, fixed horizon, spread, and slippage costs.
- Observe-once supervisor: checks demo-account status, feed availability, model output, signal direction, probability threshold, market confirmation gates, and proposal direction. It only calls a demo broker interface.
- Existing fail-closed gate returns `READY_FOR_PAPER` only, never a live-order authorization.

## Not connected yet (external dependencies required)
1. **Live news:** choose and subscribe to a licensed economic-calendar/news provider; configure API credentials in a secrets manager. Forex Factory pages are not scraped by this project.
2. **Live ticks:** choose a broker/exchange feed for the instruments and account region. One-second data is possible only if the provider actually supplies it; tick history and volume quality vary by market.
3. **AI headline interpretation:** the included structured baseline handles numeric surprises only. A real NLP/LLM model requires a selected provider/model, prompt/version controls, event taxonomy, training/evaluation data, and out-of-sample calibration.
4. **Historical backtesting:** supply point-in-time archived news including original release timestamps/revisions plus bid/ask/tick history. Survivorship, look-ahead, latency, spread, slippage, and event overlap must be modeled.
5. **Demo broker:** select broker and demo account, then implement its authenticated API adapter. No broker credentials are stored in this repository.
6. **Autonomous operation:** deploy a supervised service with persistent storage, health checks, restart policy, alerting, idempotency, rate limits, and a kill switch. The repository supervisor exposes one cycle and does not run a hosted 24/7 daemon.

## Confirmation policy
The intended state machine is `OBSERVING -> EVENT_DETECTED -> INTERPRETED -> WAITING_FOR_PRICE_CONFIRMATION -> RISK_CHECK -> READY_FOR_PAPER -> PAPER_ORDER`. Any stale/missing feed, ambiguous event, model uncertainty, conflicting direction, wide spread, high slippage, extreme volatility, absent multi-timeframe/volume confirmation, or broker error returns to `NO_TRADE`/wait.

A headline is context, not an entry. Probability is not assumed to be accurate because a model prints a number. The 90% threshold is a configurable acceptance threshold; it becomes meaningful only after calibration on sufficiently large, representative, untouched out-of-sample data. It is not a promise of 90% wins or less than 1% losses.

## Credentials required from operator
Never send secrets in chat or commit them to Git. Configure provider and demo-broker credentials locally or in the deployment platform's secret store. Vendor selection is required before concrete API adapters can be completed.
