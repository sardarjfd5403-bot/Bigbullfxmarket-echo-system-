"""Provider-neutral economic-news intelligence; no scraping or broker execution.

Connectors must supply timestamped, licensed news/calendar events. Sentiment is a
transparent baseline heuristic; production decisions require a separately
validated classifier and point-in-time historical data.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    title: str
    currency: str
    scheduled_at: datetime
    published_at: datetime
    impact: str
    actual: float | None = None
    forecast: float | None = None
    previous: float | None = None
    source: str = "unknown"
    source_url: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.title.strip():
            raise ValueError("event_id and title are required")
        if self.scheduled_at.tzinfo is None or self.published_at.tzinfo is None:
            raise ValueError("news timestamps must be timezone-aware")
        if self.impact not in {"low", "medium", "high", "unknown"}:
            raise ValueError("impact must be low, medium, high, or unknown")
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class NewsAssessment:
    event_id: str
    sentiment: str
    surprise_direction: str
    surprise: float | None
    confidence: float
    reasons: tuple[str, ...]
    tradeable_context: bool


def assess_news(event: NewsEvent, higher_is_better: bool | None = None) -> NewsAssessment:
    """Score numeric forecast surprise without assuming all indicators are good when higher."""
    if event.actual is None or event.forecast is None:
        return NewsAssessment(
            event.event_id, "unknown", "unknown", None, 0.0,
            ("Actual/forecast values unavailable; headline-only sentiment is not trusted",),
            False,
        )
    surprise = event.actual - event.forecast
    if surprise == 0:
        return NewsAssessment(
            event.event_id, "neutral", "in_line", 0.5,
            0.2, ("Actual equals forecast",), event.impact in {"medium", "high"},
        )
    if higher_is_better is None:
        return NewsAssessment(
            event.event_id, "unclassified", "above_forecast" if surprise > 0 else "below_forecast",
            surprise, 0.0,
            ("Indicator direction metadata is required before assigning positive/negative sentiment",),
            False,
        )
    positive = (surprise > 0) == higher_is_better
    sentiment = "positive" if positive else "negative"
    return NewsAssessment(
        event.event_id, sentiment,
        "above_forecast" if surprise > 0 else "below_forecast",
        surprise, 0.6,
        ("Numeric actual-versus-forecast surprise evaluated using indicator direction metadata",),
        event.impact in {"medium", "high"},
    )
