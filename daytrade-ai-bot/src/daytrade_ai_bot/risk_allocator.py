from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from daytrade_ai_bot.models import DailyCapitalPlan, RiskAllocation, RiskBucketName, RiskKnobs


DEFAULT_BUCKET_MAX_LOSS = {
    RiskBucketName.LOW: 0.5,
    RiskBucketName.MEDIUM: 1.0,
    RiskBucketName.HIGH: 2.0,
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_risk_knobs(knobs: RiskKnobs) -> dict[RiskBucketName, float]:
    """Normalize low/medium/high knob values to percentages totaling 100.

    Fine adjustment is treated as a small high-risk tilt. Positive values move
    weight toward high risk. Negative values move weight away from high risk.
    """

    low = knobs.low
    medium = knobs.medium
    high = knobs.high + knobs.fine_adjustment

    high = max(0.0, min(100.0, high))
    total = low + medium + high
    if total <= 0:
        raise ValueError("Risk knobs must produce a positive total.")

    return {
        RiskBucketName.LOW: low / total * 100.0,
        RiskBucketName.MEDIUM: medium / total * 100.0,
        RiskBucketName.HIGH: high / total * 100.0,
    }


def build_daily_capital_plan(
    *,
    trading_date: date,
    starting_cash: Decimal,
    knobs: RiskKnobs,
    target_daily_return_percent: float = 1.0,
    max_daily_loss_percent: float = 2.0,
) -> DailyCapitalPlan:
    normalized = normalize_risk_knobs(knobs)
    allocations: list[RiskAllocation] = []

    remaining = starting_cash
    bucket_order = [RiskBucketName.LOW, RiskBucketName.MEDIUM, RiskBucketName.HIGH]

    for index, bucket in enumerate(bucket_order):
        percent = normalized[bucket]
        if index == len(bucket_order) - 1:
            dollars = remaining
        else:
            dollars = _money(starting_cash * Decimal(str(percent / 100.0)))
            remaining -= dollars

        allocations.append(
            RiskAllocation(
                bucket=bucket,
                percent=percent,
                dollars=dollars,
                max_loss_percent=DEFAULT_BUCKET_MAX_LOSS[bucket],
            )
        )

    return DailyCapitalPlan(
        trading_date=trading_date,
        starting_cash=starting_cash,
        target_daily_return_percent=target_daily_return_percent,
        max_daily_loss_percent=max_daily_loss_percent,
        allocations=allocations,
    )
