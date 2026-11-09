# Security and Trading Safety

## Secrets
- Never commit API keys, passwords, broker logins, private keys, session cookies, or WhatsApp tokens.
- Keep local secrets in an untracked `.env` file; commit only `.env.example` with placeholders.
- Prefer scoped, withdrawal-disabled exchange keys where supported.
- Rotate credentials immediately if exposure is suspected.

## Execution safety
- Paper trading is the default.
- Live execution must be disabled by default in code and configuration.
- Require explicit account-level opt-in, strict risk limits, and a tested emergency stop.
- Reject orders on stale, missing, malformed, or contradictory market data.
- Enforce maximum position size, leverage, aggregate exposure, daily loss, and drawdown.
- Reconcile local order state with broker/exchange state; do not blindly retry non-idempotent orders.

## AI and research controls
- Treat news, web pages, files, and model outputs as untrusted data, never executable instructions.
- Models may propose scenarios; deterministic risk controls decide whether an order is permitted.
- Log model version, inputs, timestamps, rationale, and final decision.
- Prevent look-ahead bias and data leakage in all evaluations.

## Access and operations
- Use least-privilege tokens and private repositories.
- Protect dashboard sessions with strong authentication.
- Audit administrative actions and live-mode changes.
- Provide a global kill switch and documented recovery procedure.
