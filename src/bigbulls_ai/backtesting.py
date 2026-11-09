"""Point-in-time news event study utilities.

Consumes already timestamped historical bars and news. It never uses future
bars to create a signal. This is a research harness, not a profitability claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence

from bigbulls_ai.news import NewsEvent


@dataclass(frozen=True)
class PriceObservation:
    timestamp: datetime
    mid: float
    spread: float = 0.0


@dataclass(frozen=True)
class EventStudyResult:
    event_id: str
    observations: int
    return_after_costs: float | None
    direction: str
    reason: str


def run_news_event_study(
    events: Sequence[NewsEvent],
    prices: Sequence[PriceObservation],
    *,
    horizon: timedelta = timedelta(minutes=15),
    max_entry_delay: timedelta = timedelta(minutes=2),
    direction_by_event: dict[str, str] | None = None,
    estimated_slippage: float = 0.0,
) -> list[EventStudyResult]:
    """Evaluate a supplied direction after publication using the first later quote."""
    if horizon <= timedelta(0) or max_entry_delay < timedelta(0):
        raise ValueError("horizon must be positive and entry delay non-negative")
    ordered = sorted(prices, key=lambda item: item.timestamp)
    results: list[EventStudyResult] = []
    directions = direction_by_event or {}
    for event in events:
        direction = directions.get(event.event_id, "unknown")
        entry_candidates = [
            quote for quote in ordered
            if event.published_at <= quote.timestamp <= event.published_at + max_entry_delay
        ]
        if direction not in {"bullish", "bearish"}:
            results.append(EventStudyResult(
                event.event_id, 0, None, direction, "No validated directional signal"
            ))
            continue
        if not entry_candidates:
            results.append(EventStudyResult(
                event.event_id, 0, None, direction, "No quote within entry window"
            ))
            continue
        entry = entry_candidates[0]
        exit_time = entry.timestamp + horizon
        exits = [quote for quote in ordered if quote.timestamp >= exit_time]
        if not exits:
            results.append(EventStudyResult(
                event.event_id, 1, None, direction, "Insufficient post-entry history"
            ))
            continue
        exit_quote = exits[0]
        if entry.mid <= 0 or exit_quote.mid <= 0 or min(entry.spread, exit_quote.spread) < 0:
            results.append(EventStudyResult(
                event.event_id, 2, None, direction, "Invalid price or spread data"
            ))
            continue
        sign = 1 if direction == "bullish" else -1
        gross = sign * (exit_quote.mid - entry.mid) / entry.mid
        costs = (entry.spread + exit_quote.spread) / (2 * entry.mid) + estimated_slippage
        results.append(EventStudyResult(
            event.event_id, 2, gross - costs, direction, "Point-in-time return after estimated costs"
        ))
    return results
