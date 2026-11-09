"""Continuous observe/wait/confirm supervisor; paper execution only."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from bigbulls_ai.execution_gate import (
    ExecutionAssessment,
    MarketConditions,
    assess_execution_readiness,
)
from bigbulls_ai.integrations import DemoBroker, NewsInterpreter, NewsProvider, TickDataProvider
from bigbulls_ai.risk import TradeProposal


@dataclass(frozen=True)
class SupervisorResult:
    state: str
    reason: str
    orders_submitted: int = 0


class AutonomousSupervisor:
    """Observe feeds and submit only when every gate passes and broker is demo."""

    def __init__(
        self,
        news_provider: NewsProvider,
        tick_provider: TickDataProvider,
        interpreter: NewsInterpreter,
        broker: DemoBroker,
    ) -> None:
        self.news_provider = news_provider
        self.tick_provider = tick_provider
        self.interpreter = interpreter
        self.broker = broker

    def observe_once(
        self,
        symbols: Sequence[str],
        since: datetime,
        until: datetime,
        conditions_by_symbol: dict[str, MarketConditions],
        proposals_by_symbol: dict[str, TradeProposal],
        quantity_by_symbol: dict[str, float],
    ) -> SupervisorResult:
        """One observation cycle. Scheduler/daemon lifecycle belongs to deployment."""
        if not self.broker.account_is_demo():
            return SupervisorResult("HALTED", "Broker did not confirm a demo account")
        if until < since or since.tzinfo is None or until.tzinfo is None:
            return SupervisorResult("NO_TRADE", "Invalid or timezone-naive observation window")
        try:
            events = self.news_provider.fetch_events(since, until)
            ticks = self.tick_provider.latest_ticks(symbols)
        except Exception as exc:
            return SupervisorResult("NO_TRADE", f"Provider unavailable: {type(exc).__name__}")
        if not ticks:
            return SupervisorResult("NO_TRADE", "No live ticks received")
        if not events:
            return SupervisorResult("OBSERVING", "No new news; continue waiting for opportunities")
        interpreted = []
        try:
            for event in events:
                result = self.interpreter.interpret(event)
                result.validate()
                interpreted.append(result)
        except Exception as exc:
            return SupervisorResult("NO_TRADE", f"News interpretation failed: {type(exc).__name__}")
        orders = 0
        for signal in interpreted:
            symbol = signal.instrument
            if symbol not in symbols or symbol not in proposals_by_symbol:
                continue
            conditions = conditions_by_symbol.get(symbol)
            quantity = quantity_by_symbol.get(symbol, 0.0)
            if conditions is None or quantity <= 0:
                continue
            if signal.direction not in {"bullish", "bearish"}:
                continue
            if signal.probability < 0.90:
                continue
            assessment: ExecutionAssessment = assess_execution_readiness(conditions)
            if assessment.decision != "READY_FOR_PAPER":
                continue
            proposal = proposals_by_symbol[symbol]
            if (signal.direction == "bullish" and proposal.side != "buy") or (
                signal.direction == "bearish" and proposal.side != "sell"
            ):
                continue
            try:
                result = self.broker.submit_demo_order(proposal, quantity)
            except Exception:
                return SupervisorResult("NO_TRADE", "Demo broker submission failed", orders)
            if result.accepted:
                orders += 1
        if orders:
            return SupervisorResult("PAPER_ORDERS_SUBMITTED", "All configured confirmation gates passed", orders)
        return SupervisorResult("OBSERVING", "No opportunity passed every confirmation gate")
