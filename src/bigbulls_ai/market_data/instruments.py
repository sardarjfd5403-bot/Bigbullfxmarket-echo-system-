"""Canonical instrument registry; provider symbols are mapped separately."""

from dataclasses import dataclass
from enum import StrEnum


class AssetClass(StrEnum):
    FOREX = "forex"
    CRYPTO = "crypto"
    METAL = "metal"
    INDEX = "index"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_class: AssetClass
    base: str
    quote: str
    price_precision: int
    quantity_precision: int = 2

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty and uppercase")
        if not self.base or not self.quote:
            raise ValueError("base and quote are required")
        if self.price_precision < 0 or self.quantity_precision < 0:
            raise ValueError("precision values cannot be negative")


# Small examples only. Production symbols must come from the selected broker/exchange.
DEFAULT_INSTRUMENTS = (
    Instrument("EURUSD", AssetClass.FOREX, "EUR", "USD", 5),
    Instrument("GBPUSD", AssetClass.FOREX, "GBP", "USD", 5),
    Instrument("XAUUSD", AssetClass.METAL, "XAU", "USD", 2),
    Instrument("BTCUSDT", AssetClass.CRYPTO, "BTC", "USDT", 2),
    Instrument("ETHUSDT", AssetClass.CRYPTO, "ETH", "USDT", 2),
    Instrument("US100", AssetClass.INDEX, "US100", "USD", 2),
)


def get_instrument(symbol: str) -> Instrument:
    normalized = symbol.strip().upper()
    for instrument in DEFAULT_INSTRUMENTS:
        if instrument.symbol == normalized:
            return instrument
    raise KeyError(f"Unknown instrument: {symbol}")
