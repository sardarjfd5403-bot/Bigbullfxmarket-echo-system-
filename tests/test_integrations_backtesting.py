from datetime import UTC, datetime, timedelta

from bigbulls_ai.backtesting import PriceObservation, run_news_event_study
from bigbulls_ai.integrations import NewsModelOutput
from bigbulls_ai.news import NewsEvent
from bigbulls_ai.news_model import StructuredNewsInterpreter


def event():
    now = datetime(2026, 11, 9, 12, tzinfo=UTC)
    return NewsEvent(
        "us-cpi-1", "US CPI", "USD", now, now, "high",
        actual=3.0, forecast=3.2, previous=3.1, source="fixture",
    )


def test_structured_news_interpreter_uses_indicator_direction():
    result = StructuredNewsInterpreter({"us cpi": False}).interpret(event())
    assert result.direction == "bullish"
    assert result.model_version == "structured-surprise-v1"


def test_unknown_news_is_not_forced_into_direction():
    result = StructuredNewsInterpreter({}).interpret(event())
    assert result.direction == "unknown"
    assert result.probability == 0


def test_news_event_study_uses_only_quotes_after_publication_and_costs():
    item = event()
    prices = [
        PriceObservation(item.published_at - timedelta(seconds=1), 100.0, 0.1),
        PriceObservation(item.published_at + timedelta(seconds=10), 100.0, 0.1),
        PriceObservation(item.published_at + timedelta(minutes=16), 102.0, 0.1),
    ]
    results = run_news_event_study(
        [item], prices, direction_by_event={item.event_id: "bullish"},
        estimated_slippage=0.0001,
    )
    assert results[0].observations == 2
    assert results[0].return_after_costs is not None
    assert results[0].return_after_costs < 0.02


def test_event_study_does_not_make_up_unknown_direction():
    results = run_news_event_study([event()], [])
    assert results[0].return_after_costs is None
    assert results[0].reason == "No validated directional signal"


def test_news_model_output_rejects_invalid_probability():
    output = NewsModelOutput("id", "USD", "bullish", 1.2, "v1", ())
    try:
        output.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid probability should fail validation")
