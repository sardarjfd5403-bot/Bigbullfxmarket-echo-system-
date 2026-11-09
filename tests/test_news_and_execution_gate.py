from datetime import UTC, datetime, timedelta

import pytest

from bigbulls_ai.news import NewsEvent, assess_news, event_pair_bias
from bigbulls_ai.execution_gate import MarketConditions, assess_execution_readiness


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)


def event(**kwargs):
    values = dict(
        event_id="us-cpi-1", title="US CPI", currency="USD",
        scheduled_at=NOW, published_at=NOW, impact="high",
        actual=3.1, forecast=3.0, previous=2.9, source="test",
    )
    values.update(kwargs)
    return NewsEvent(**values)


def test_news_numeric_surprise_requires_indicator_direction():
    result = assess_news(event(), higher_is_better=None)
    assert result.sentiment == "unclassified"
    assert not result.tradeable_context


def test_news_positive_surprise_with_direction_metadata():
    result = assess_news(event(), higher_is_better=True)
    assert result.sentiment == "positive"
    assert result.tradeable_context
    assert event_pair_bias(event(), result, "EUR", "USD") == "bearish"
    assert event_pair_bias(event(), result, "USD", "JPY") == "bullish"


def test_headline_without_numbers_is_not_trusted():
    result = assess_news(event(actual=None, forecast=None))
    assert result.sentiment == "unknown"
    assert not result.tradeable_context


def test_naive_news_timestamp_rejected():
    with pytest.raises(ValueError):
        event(published_at=datetime(2026, 11, 9, 12, 0))


def valid_conditions(**kwargs):
    values = dict(
        observed_at=NOW, spread_bps=1.0, estimated_slippage_bps=1.0,
        current_bar_range_atr=1.2, seconds_since_high_impact_release=90,
        price_confirmation=True, multi_timeframe_confirmation=True,
        volume_confirmation=True, calibrated_probability=0.92,
        calibration_valid=True, validation_sample_size=1000,
        model_validation_date=NOW - timedelta(days=2), news_direction_confirmed=True,
    )
    values.update(kwargs)
    return MarketConditions(**values)


def test_execution_gate_passes_only_to_paper_readiness():
    result = assess_execution_readiness(valid_conditions())
    assert result.decision == "READY_FOR_PAPER"


@pytest.mark.parametrize("override", [
    {"seconds_since_high_impact_release": 5},
    {"current_bar_range_atr": 4.0},
    {"spread_bps": 8.0},
    {"estimated_slippage_bps": 5.0},
    {"price_confirmation": False},
    {"multi_timeframe_confirmation": False},
    {"volume_confirmation": False},
    {"calibrated_probability": 0.75},
    {"calibration_valid": False},
    {"validation_sample_size": 20},
])
def test_execution_gate_fails_closed(override):
    result = assess_execution_readiness(valid_conditions(**override))
    assert result.decision == "NO_TRADE"
    assert result.accepted_probability is None
