"""Conservative all-family confluence gate. This module does not place orders."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from bigbulls_ai.research.models import StrategySignal


@dataclass(frozen=True)
class DecisionAssessment:
    decision: str
    direction: str
    score: float
    agreement: float
    bullish_families: tuple[str, ...]
    bearish_families: tuple[str, ...]
    reasons: tuple[str, ...]


def assess_confluence(
    signals_by_timeframe: Mapping[str, Sequence[StrategySignal]],
    min_agreement: float = 0.75,
    min_families: int = 4,
    min_score: float = 0.55,
) -> DecisionAssessment:
    """Require broad independent-family agreement; otherwise explicitly abstain.

    The score is a heuristic ranking value, never a calibrated win probability.
    """
    latest: dict[str, StrategySignal] = {}
    for signals in signals_by_timeframe.values():
        for signal in signals:
            if signal.direction in {"bullish", "bearish"}:
                # Keep the strongest absolute observation for each family to avoid
                # counting the same indicator repeatedly across correlated timeframes.
                if signal.name not in latest or abs(signal.score) > abs(latest[signal.name].score):
                    latest[signal.name] = signal
    if not latest:
        return DecisionAssessment("NO_TRADE", "neutral", 0.0, 0.0, (), (), ("No directional strategy evidence",))
    bullish = tuple(sorted(name for name, s in latest.items() if s.direction == "bullish"))
    bearish = tuple(sorted(name for name, s in latest.items() if s.direction == "bearish"))
    total = len(latest)
    winning = max(len(bullish), len(bearish))
    agreement = winning / total
    direction = "bullish" if len(bullish) > len(bearish) else "bearish" if len(bearish) > len(bullish) else "neutral"
    signed = sum(s.score for s in latest.values())
    score = min(1.0, abs(signed) / max(1.0, sum(abs(s.score) for s in latest.values())))
    reasons = []
    if direction == "neutral":
        reasons.append("Strategy families are tied")
    if agreement < min_agreement:
        reasons.append(f"Agreement {agreement:.0%} is below required {min_agreement:.0%}")
    if winning < min_families:
        reasons.append(f"Only {winning} agreeing families; at least {min_families} required")
    if score < min_score:
        reasons.append(f"Directional score {score:.2f} is below required {min_score:.2f}")
    decision = "RESEARCH_CANDIDATE" if not reasons else "NO_TRADE"
    return DecisionAssessment(decision, direction, score, agreement, bullish, bearish, tuple(reasons))
