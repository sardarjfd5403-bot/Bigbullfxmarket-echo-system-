"""Fail-closed risk primitives; no broker execution is implemented here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_risk_fraction: float = 0.005
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.05
    max_open_positions: int = 3

    def validate(self) -> None:
        for name, value in (
            ("max_risk_fraction", self.max_risk_fraction),
            ("max_daily_loss_fraction", self.max_daily_loss_fraction),
            ("max_drawdown_fraction", self.max_drawdown_fraction),
        ):
            if not 0 < value < 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be at least 1.")


@dataclass(frozen=True)
class TradeProposal:
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float


def validate_proposal(proposal: TradeProposal) -> None:
    """Validate basic proposal integrity, not profitability or execution suitability."""
    if not proposal.symbol.strip():
        raise ValueError("Symbol is required.")
    if proposal.side not in {"buy", "sell"}:
        raise ValueError("Side must be 'buy' or 'sell'.")
    if min(proposal.entry, proposal.stop_loss, proposal.take_profit) <= 0:
        raise ValueError("Prices must be positive.")
    if proposal.side == "buy" and not proposal.stop_loss < proposal.entry < proposal.take_profit:
        raise ValueError("For a buy, require stop_loss < entry < take_profit.")
    if proposal.side == "sell" and not proposal.take_profit < proposal.entry < proposal.stop_loss:
        raise ValueError("For a sell, require take_profit < entry < stop_loss.")
