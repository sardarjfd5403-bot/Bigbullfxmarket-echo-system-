import pytest

from bigbulls_ai.config import Settings
from bigbulls_ai.risk import RiskLimits, TradeProposal, validate_proposal


def test_live_trading_is_disabled_by_default():
    settings = Settings()
    assert settings.trading_mode == "paper"
    assert settings.live_trading_enabled is False


def test_live_mode_fails_closed_without_explicit_enablement():
    with pytest.raises(ValueError):
        Settings(trading_mode="live", live_trading_enabled=False).validate()


def test_risk_limits_reject_invalid_fraction():
    with pytest.raises(ValueError):
        RiskLimits(max_risk_fraction=1.5).validate()


def test_valid_buy_proposal():
    validate_proposal(TradeProposal("EURUSD", "buy", 1.1, 1.09, 1.12))


def test_invalid_buy_proposal_rejected():
    with pytest.raises(ValueError):
        validate_proposal(TradeProposal("EURUSD", "buy", 1.1, 1.11, 1.12))
