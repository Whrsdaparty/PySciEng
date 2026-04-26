from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from daytrade_ai_bot.models import RiskBucketName, RiskKnobs
from daytrade_ai_bot.risk_allocator import build_daily_capital_plan, normalize_risk_knobs


def test_normalized_knobs_sum_to_100() -> None:
    result = normalize_risk_knobs(RiskKnobs(low=25, medium=50, high=25))
    assert pytest.approx(sum(result.values())) == 100.0


def test_build_daily_capital_plan_allocates_all_cash() -> None:
    plan = build_daily_capital_plan(
        trading_date=date(2026, 4, 25),
        starting_cash=Decimal("1000.00"),
        knobs=RiskKnobs(low=40, medium=40, high=20),
    )

    assert sum(item.dollars for item in plan.allocations) == Decimal("1000.00")
    assert {item.bucket for item in plan.allocations} == {
        RiskBucketName.LOW,
        RiskBucketName.MEDIUM,
        RiskBucketName.HIGH,
    }


def test_zero_knobs_rejected() -> None:
    with pytest.raises(ValueError):
        RiskKnobs(low=0, medium=0, high=0)
