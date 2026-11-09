from datetime import UTC, datetime

import pytest

from bigbulls_ai.market_data.instruments import AssetClass, Instrument, get_instrument
from bigbulls_ai.market_data.models import Candle


def test_registry_resolves_supported_examples():
    assert get_instrument("eurusd").asset_class == AssetClass.FOREX
    assert get_instrument("XAUUSD").asset_class == AssetClass.METAL


def test_registry_rejects_unknown_symbol():
    with pytest.raises(KeyError):
        get_instrument("NOTREAL")


def test_instrument_rejects_lowercase_symbol():
    with pytest.raises(ValueError):
        Instrument("eurusd", AssetClass.FOREX, "EUR", "USD", 5)


def test_candle_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        Candle("EURUSD", "M5", datetime(2026, 1, 1), 1.1, 1.2, 1.0, 1.15, 100)


def test_candle_validates_ohlc_and_volume_provenance():
    candle = Candle("EURUSD", "M5", datetime(2026, 1, 1, tzinfo=UTC),
                    1.1, 1.2, 1.0, 1.15, 120, "tick", "demo")
    assert candle.timestamp_utc.tzinfo == UTC
    with pytest.raises(ValueError):
        Candle("EURUSD", "M5", datetime(2026, 1, 1, tzinfo=UTC),
               1.1, 1.05, 1.0, 1.15, 120)
