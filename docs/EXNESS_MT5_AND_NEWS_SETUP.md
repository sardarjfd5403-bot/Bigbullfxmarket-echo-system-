# Exness MT5 Demo + Trading Economics setup

## What is already in the repository
- `TradingEconomicsCalendar`: documented economic-calendar REST adapter.
- `MT5DemoAdapter`: Windows MetaTrader 5 terminal adapter for bid/ask ticks and demo orders.
- The MT5 adapter refuses to connect if the terminal account is not marked DEMO.
- Structured numeric-surprise baseline and event-study backtest harness.
- No credentials are stored in Git. No live-account order path is enabled.

## 1. Trading Economics API
1. Create an account at https://developer.tradingeconomics.com/.
2. Review the current plan and trial terms at https://tradingeconomics.com/api/pricing.aspx. Do not start a paid trial/subscription without reviewing renewal billing and getting approval.
3. Generate an API key in the provider dashboard.
4. Store it locally as `TRADING_ECONOMICS_API_KEY` or in GitHub repository Settings -> Secrets and variables -> Actions -> New repository secret.
5. Optional: set `TRADING_ECONOMICS_NAIVE_TIMEZONE`. The adapter defaults to UTC for timezone-naive calendar values; confirm the provider's timezone convention for the subscribed endpoint before production use.

## 2. Exness MT5 demo terminal
1. Install MetaTrader 5 on a Windows PC or Windows VPS that will remain powered on.
2. In MT5, add/find Exness as broker and sign in to an Exness DEMO account. Confirm the terminal clearly shows a demo account.
3. Keep Market Watch enabled and select the instruments to monitor. Broker symbol suffixes (for example, .m or similar) must match the configured symbols exactly.
4. Install Python 3.11+ and this project on that Windows machine:
   `py -m pip install -e ".[dev,mt5]"`
5. Set `MT5_TERMINAL_PATH` to the installed `terminal64.exe` path if automatic terminal discovery does not work.
6. Keep MT5 terminal open and logged into DEMO. Do not provide passwords in chat or commit them to Git.

## 3. Local validation (Windows)
Run the repository tests first:
`py -m pytest`

Then, after setting the API key and terminal path, run a local integration smoke test using only the Exness DEMO terminal. The GitHub Actions Linux runner can lint/test the provider-neutral code but cannot operate the user's Windows MT5 desktop terminal.

## Important current limitations
- The Trading Economics adapter is implemented but cannot fetch real data until a valid subscribed API key is configured.
- The MT5 adapter is implemented but cannot connect until installed and run on the user's Windows machine with an Exness DEMO terminal.
- StructuredNewsInterpreter is a conservative numeric-surprise baseline, not a general AI headline/NLP model. It returns low confidence and must not produce trades on its own. A separately selected and out-of-sample calibrated model is still required.
- Historical event-study code needs licensed point-in-time event history and matching tick/bid-ask history to produce credible results.
- The autonomous supervisor is a single observation cycle, not yet a persistent 24/7 service. Deployment needs scheduling, durable state, idempotency, monitoring, alerts, and a kill switch.
- Demo orders are the only supported execution target. Do not enable live execution.
