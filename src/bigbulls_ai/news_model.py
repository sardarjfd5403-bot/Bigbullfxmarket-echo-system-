"""Conservative baseline news interpretation.

This deterministic baseline does NOT claim to understand arbitrary headlines.
It classifies only structured macro events with supplied indicator metadata.
Replace with a versioned NLP model only after point-in-time training and
out-of-sample calibration. Unknown is a valid and preferred outcome.
"""
from __future__ import annotations

from bigbulls_ai.integrations import NewsModelOutput
from bigbulls_ai.news import NewsEvent, assess_news


class StructuredNewsInterpreter:
    """Transparent numeric-surprise classifier; no unsupported headline guesses."""

    def __init__(self, indicator_directions: dict[str, bool]) -> None:
        self._indicator_directions = dict(indicator_directions)

    def interpret(self, event: NewsEvent) -> NewsModelOutput:
        assessment = assess_news(
            event,
            higher_is_better=self._indicator_directions.get(event.title.casefold()),
        )
        direction = "unknown"
        if assessment.sentiment == "positive":
            direction = "bullish"
        elif assessment.sentiment == "negative":
            direction = "bearish"
        elif assessment.sentiment == "neutral":
            direction = "neutral"
        result = NewsModelOutput(
            event_id=event.event_id,
            instrument=event.currency.upper(),
            direction=direction,
            probability=assessment.confidence,
            model_version="structured-surprise-v1",
            evidence=assessment.reasons,
        )
        result.validate()
        return result
