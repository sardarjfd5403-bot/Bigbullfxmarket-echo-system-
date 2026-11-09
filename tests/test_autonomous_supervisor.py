from datetime import UTC, datetime

from bigbulls_ai.autonomous import AutonomousSupervisor
from bigbulls_ai.execution_gate import MarketConditions
from bigbulls_ai.integrations import NewsModelOutput
from bigbulls_ai.news import NewsEvent
from bigbulls_ai.paper_broker import InMemoryDemoBroker
from bigbulls_ai.risk import TradeProposal


class FakeNews:
    def fetch_events(self, since, until):
        return [NewsEvent("n1", "USD data", "USD", since, since, "high", 3.0, 2.0)]


class FakeTicks:
    def latest_ticks(self, symbols):
        return [object()]


class FakeInterpreter:
    def interpret(self, event):
        return NewsModelOutput(event.event_id, "USD", "bullish", 0.95, "test-v1", ("fixture",))


def conditions(now):
    return MarketConditions(
        observed_at=now,
        spread_bps=1.0,
        estimated_slippage_bps=0.5,
        current_bar_range_atr=1.0,
        seconds_since_high_impact_release=60.0,
        price_confirmation=True,
        multi_timeframe_confirmation=True,
        volume_confirmation=True,
        calibrated_probability=0.95,
        calibration_valid=True,
        validation_sample_size=1000,
        model_validation_date=now,
        news_direction_confirmed=True,
    )


def test_supervisor_submits_only_to_explicit_demo_broker():
    now = datetime(2026, 11, 9, 12, tzinfo=UTC)
    broker = InMemoryDemoBroker()
    supervisor = AutonomousSupervisor(FakeNews(), FakeTicks(), FakeInterpreter(), broker)
    result = supervisor.observe_once(
        ["USD"], now, now,
        {"USD": conditions(now)},
        {"USD": TradeProposal("USD", "buy", 100.0, 99.0, 102.0)},
        {"USD": 0.01},
    )
    assert result.state == "PAPER_ORDERS_SUBMITTED"
    assert result.orders_submitted == 1
    assert len(broker.orders) == 1


def test_supervisor_halts_if_account_is_not_demo():
    now = datetime(2026, 11, 9, 12, tzinfo=UTC)
    broker = InMemoryDemoBroker(demo=False)
    supervisor = AutonomousSupervisor(FakeNews(), FakeTicks(), FakeInterpreter(), broker)
    result = supervisor.observe_once(["USD"], now, now, {}, {}, {})
    assert result.state == "HALTED"
    assert not broker.orders


def test_supervisor_waits_when_no_confirmation():
    now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
    broker = InMemoryDemoBroker()
    supervisor = AutonomousSupervisor(FakeNews(), FakeTicks(), FakeInterpreter(), broker)
    unsafe = conditions(now).__class__(
        observed_at=now, spread_bps=20.0, estimated_slippage_bps=0.5,
        current_bar_range_atr=1.0, seconds_since_high_impact_release=60.0,
        price_confirmation=False, multi_timeframe_confirmation=True,
        volume_confirmation=True, calibrated_probability=0.95, calibration_valid=True,
        validation_sample_size=1000, model_validation_date=now, news_direction_confirmed=True,
    )
    result = supervisor.observe_once(
        ["USD"], now, now, {"USD": unsafe},
        {"USD": TradeProposal("USD", "buy", 100.0, 99.0, 102.0)}, {"USD": 0.01},
    )
    assert result.state == "OBSERVING"
    assert result.orders_submitted == 0
    assert not broker.orders
