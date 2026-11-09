"""In-memory paper broker. It never connects to a live account or venue."""
from dataclasses import dataclass, field

from bigbulls_ai.integrations import BrokerOrderResult
from bigbulls_ai.risk import TradeProposal, validate_proposal


@dataclass
class InMemoryDemoBroker:
    """Deterministic demo-only broker stub for end-to-end application tests."""

    demo: bool = True
    orders: list[tuple[TradeProposal, float]] = field(default_factory=list)

    def account_is_demo(self) -> bool:
        return self.demo

    def submit_demo_order(self, proposal: TradeProposal, quantity: float) -> BrokerOrderResult:
        if not self.demo:
            return BrokerOrderResult(False, None, "rejected", "Live accounts are not supported")
        if quantity <= 0:
            return BrokerOrderResult(False, None, "rejected", "Quantity must be positive")
        validate_proposal(proposal)
        self.orders.append((proposal, quantity))
        return BrokerOrderResult(
            True, f"paper-{len(self.orders)}", "accepted", "Recorded in local paper ledger"
        )
