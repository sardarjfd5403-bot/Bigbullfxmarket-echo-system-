# Market Data Contract

The first implementation step standardizes market data before connecting vendors.

- All timestamps must be timezone-aware; consumers should normalize to UTC.
- OHLC prices must be positive and internally consistent.
- Volume must include provenance: unknown, tick, base, quote, or contracts.
- Spot FX tick volume must never be mislabeled as consolidated traded volume.
- Provider symbol names must map to canonical instrument identifiers.
- Historical queries use a half-open interval [start, end) and return chronological data.
- Adapters must report missing intervals, duplicate candles, stale quotes, and provider identity.

The sample registry is illustrative, not a guarantee that every broker supports each symbol. Contract size, tick size, sessions, trading calendar, and symbol mappings must be loaded from the selected provider before execution is enabled.
