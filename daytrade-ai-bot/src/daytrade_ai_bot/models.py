from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RiskBucketName(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProfileMode(str, Enum):
    RESEARCH = "research"
    LIVE_TRACKING = "live_tracking"


class RiskKnobs(BaseModel):
    """Raw user-facing knob values. Values do not need to sum to 100."""

    low: float = Field(ge=0, le=100)
    medium: float = Field(ge=0, le=100)
    high: float = Field(ge=0, le=100)
    fine_adjustment: float = Field(default=0.0, ge=-5.0, le=5.0)

    @model_validator(mode="after")
    def at_least_one_knob_enabled(self) -> "RiskKnobs":
        if self.low + self.medium + self.high <= 0:
            raise ValueError("At least one risk knob must be greater than zero.")
        return self


class RiskAllocation(BaseModel):
    bucket: RiskBucketName
    percent: float = Field(ge=0, le=100)
    dollars: Decimal = Field(ge=Decimal("0"))
    max_loss_percent: float = Field(ge=0, le=100)


class DailyCapitalPlan(BaseModel):
    trading_date: date
    starting_cash: Decimal = Field(gt=Decimal("0"))
    target_daily_return_percent: float = Field(default=1.0, ge=0, le=100)
    max_daily_loss_percent: float = Field(default=2.0, ge=0, le=100)
    allocations: list[RiskAllocation]

    @field_validator("allocations")
    @classmethod
    def require_three_buckets(cls, value: list[RiskAllocation]) -> list[RiskAllocation]:
        buckets = {item.bucket for item in value}
        expected = {RiskBucketName.LOW, RiskBucketName.MEDIUM, RiskBucketName.HIGH}
        if buckets != expected:
            raise ValueError("Allocations must contain low, medium, and high buckets.")
        return value


class Position(BaseModel):
    symbol: str
    shares: Decimal = Field(gt=Decimal("0"))
    starting_price: Decimal = Field(gt=Decimal("0"))
    current_price: Decimal | None = Field(default=None, gt=Decimal("0"))
    opened_at: datetime
    risk_bucket: RiskBucketName
    notes: str = ""

    @property
    def cost_basis(self) -> Decimal:
        return self.shares * self.starting_price

    @property
    def market_value(self) -> Decimal | None:
        if self.current_price is None:
            return None
        return self.shares * self.current_price

    @property
    def unrealized_pl(self) -> Decimal | None:
        if self.market_value is None:
            return None
        return self.market_value - self.cost_basis


class TradingProfile(BaseModel):
    name: str
    mode: ProfileMode
    starting_cash: Decimal = Field(gt=Decimal("0"))
    cash_available: Decimal = Field(ge=Decimal("0"))
    positions: list[Position] = Field(default_factory=list)


class StrategyInsight(BaseModel):
    source: str
    category: Literal["price_action", "volume", "news", "macro", "risk", "technical", "manual"]
    summary: str
    confidence: float = Field(ge=0, le=1)


class StrategyReport(BaseModel):
    created_at: datetime
    profile_name: str
    plan: DailyCapitalPlan
    insights: list[StrategyInsight]
    warnings: list[str] = Field(default_factory=list)
    human_review_required: bool = True
