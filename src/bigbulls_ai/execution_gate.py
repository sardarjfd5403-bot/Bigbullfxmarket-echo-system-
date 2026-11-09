"""Fail-closed event/volatility/confirmation gate before any execution adapter.

A model probability is accepted only when supplied by an externally calibrated
model and accompanied by its validation metadata. This module never predicts
or fabricates a probability and never submits orders.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class MarketConditions:
    observed_at: datetime
    spread_bps: float
    estimated_slippage_bps: float
    current_bar_range_atr: float
    seconds_since_high_impact_release: float | None
    price_confirmation: bool
    multi_timeframe_confirmation: bool
    volume_confirmation: bool
    calibrated_probability: float | None = None
    calibration_valid: bool = False
    validation_sample_size: int = 0
    model_validation_date: datetime | None = None


@dataclass(frozen=True)
class ExecutionAssessment:
    decision: str
    reasons: tuple[str, ...]
    accepted_probability: float | None


def assess_execution_readiness(
    conditions: MarketConditions,
    *,
    minimum_probability: float = 0.90,
    maximum_spread_bps: float = 3.0,
    maximum_slippage_bps: float = 2.0,
    maximum_bar_range_atr: float = 3.0,
    news_cooldown_seconds: float = 30.0,
    minimum_validation_samples: int = 500,
    maximum_model_age_days: int = 30,
) -> ExecutionAssessment:
    """Return READY_FOR_PAPER only if every explicit gate passes."""
    reasons: list[str] = []
    if conditions.observed_at.tzinfo is None:
        reasons.append("Observation timestamp must be timezone-aware")
    if conditions.spread_bps < 0 or conditions.estimated_slippage_bps < 0:
        reasons.append("Spread/slippage inputs cannot be negative")
    if conditions.spread_bps > maximum_spread_bps:
        reasons.append("Spread exceeds configured limit")
    if conditions.estimated_slippage_bps > maximum_slippage_bps:
        reasons.append("Estimated slippage exceeds configured limit")
    if conditions.current_bar_range_atr <= 0:
        reasons.append("Invalid ATR-normalized bar range")
    elif conditions.current_bar_range_atr > maximum_bar_range_atr:
        reasons.append("Extreme volatility: wait for range normalization and fresh confirmation")
    if conditions.seconds_since_high_impact_release is not None:
        if conditions.seconds_since_high_impact_release < news_cooldown_seconds:
            reasons.append("High-impact news cooldown is active")
    if not conditions.price_confirmation:
        reasons.append("No post-news price confirmation")
    if not conditions.multi_timeframe_confirmation:
        reasons.append("Multi-timeframe confirmation missing")
    if not conditions.volume_confirmation:
        reasons.append("Volume/liquidity confirmation missing")
    probability = conditions.calibrated_probability
    if probability is None or not 0 <= probability <= 1:
        reasons.append("No valid calibrated probability supplied")
    elif probability < minimum_probability:
        reasons.append("Calibrated probability below configured threshold")
    if not conditions.calibration_valid:
        reasons.append("Model calibration/out-of-sample validation not approved")
    if conditions.validation_sample_size < minimum_validation_samples:
        reasons.append("Insufficient out-of-sample validation sample")
    if conditions.model_validation_date is None or conditions.model_validation_date.tzinfo is None:
        reasons.append("Missing timezone-aware model validation date")
    elif conditions.observed_at.tzinfo is not None:
        age = conditions.observed_at - conditions.model_validation_date
        if age > timedelta(days=maximum_model_age_days):
            reasons.append("Model validation is stale")
        if age < timedelta(days=-1):
            reasons.append("Model validation date is in the future")
    if reasons:
        return ExecutionAssessment("NO_TRADE", tuple(reasons), None)
    return ExecutionAssessment("READY_FOR_PAPER", ("All configured readiness gates passed",), probability)
