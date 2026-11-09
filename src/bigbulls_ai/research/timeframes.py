"""Supported chart intervals; availability depends on each data provider."""

TIMEFRAME_SECONDS: dict[str, int] = {
    "1s": 1, "5s": 5, "10s": 10, "15s": 15, "30s": 30,
    "1m": 60, "2m": 120, "3m": 180, "5m": 300, "10m": 600,
    "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200,
    "4h": 14400, "6h": 21600, "8h": 28800, "12h": 43200,
    "1d": 86400, "1w": 604800, "1mo": 2592000,
}


def timeframe_seconds(timeframe: str) -> int:
    try:
        return TIMEFRAME_SECONDS[timeframe.lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported timeframe: {timeframe}") from exc
