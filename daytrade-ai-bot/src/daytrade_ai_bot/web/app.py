from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from daytrade_ai_bot.models import RiskKnobs
from daytrade_ai_bot.risk_allocator import build_daily_capital_plan
from daytrade_ai_bot.storage import (
    DatabaseKind,
    initialize_all_databases,
    list_equity_snapshots,
    list_trades,
    record_equity_snapshot,
    record_trade,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PACKAGE_ROOT / "web"
STATIC_ROOT = WEB_ROOT / "static"
TEMPLATE_ROOT = WEB_ROOT / "templates"

app = FastAPI(title="Daytrade AI Bot", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


class AllocationRequest(BaseModel):
    starting_cash: Decimal = Field(gt=Decimal("0"))
    low: float = Field(ge=0, le=100)
    medium: float = Field(ge=0, le=100)
    high: float = Field(ge=0, le=100)
    fine_adjustment: float = Field(default=0.0, ge=-5.0, le=5.0)
    target_daily_return_percent: float = Field(default=1.0, ge=0, le=100)
    max_daily_loss_percent: float = Field(default=2.0, ge=0, le=100)


class TradeRequest(BaseModel):
    profile: DatabaseKind
    symbol: str = Field(min_length=1, max_length=12)
    side: Literal["buy", "sell"]
    shares: Decimal = Field(gt=Decimal("0"))
    price: Decimal = Field(gt=Decimal("0"))
    fees: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    risk_bucket: Literal["low", "medium", "high"]
    strategy_name: str = ""
    notes: str = ""


class EquitySnapshotRequest(BaseModel):
    profile: DatabaseKind
    cash: Decimal = Field(ge=Decimal("0"))
    open_position_value: Decimal = Field(ge=Decimal("0"))
    realized_gain_total: Decimal
    unrealized_gain_total: Decimal
    notes: str = ""


@app.on_event("startup")
def startup() -> None:
    initialize_all_databases()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(TEMPLATE_ROOT / "index.html")


@app.post("/api/allocate")
def allocate(request: AllocationRequest) -> dict[str, object]:
    plan = build_daily_capital_plan(
        trading_date=date.today(),
        starting_cash=request.starting_cash,
        knobs=RiskKnobs(
            low=request.low,
            medium=request.medium,
            high=request.high,
            fine_adjustment=request.fine_adjustment,
        ),
        target_daily_return_percent=request.target_daily_return_percent,
        max_daily_loss_percent=request.max_daily_loss_percent,
    )

    return {
        "trading_date": plan.trading_date.isoformat(),
        "starting_cash": str(plan.starting_cash),
        "target_daily_return_percent": plan.target_daily_return_percent,
        "max_daily_loss_percent": plan.max_daily_loss_percent,
        "allocations": [
            {
                "bucket": allocation.bucket.value,
                "percent": round(allocation.percent, 4),
                "dollars": str(allocation.dollars),
                "max_loss_percent": allocation.max_loss_percent,
            }
            for allocation in plan.allocations
        ],
        "human_review_required": True,
    }


@app.post("/api/trades")
def create_trade(request: TradeRequest) -> dict[str, object]:
    trade_id = record_trade(
        kind=request.profile,
        symbol=request.symbol,
        side=request.side,
        shares=request.shares,
        price=request.price,
        fees=request.fees,
        risk_bucket=request.risk_bucket,
        strategy_name=request.strategy_name,
        notes=request.notes,
    )
    return {"id": trade_id, "profile": request.profile, "status": "recorded"}


@app.get("/api/trades/{profile}")
def get_trade_history(profile: DatabaseKind) -> dict[str, object]:
    return {"profile": profile, "trades": list_trades(profile)}


@app.post("/api/equity-snapshots")
def create_equity_snapshot(request: EquitySnapshotRequest) -> dict[str, object]:
    snapshot_id = record_equity_snapshot(
        kind=request.profile,
        cash=request.cash,
        open_position_value=request.open_position_value,
        realized_gain_total=request.realized_gain_total,
        unrealized_gain_total=request.unrealized_gain_total,
        notes=request.notes,
    )
    return {"id": snapshot_id, "profile": request.profile, "status": "recorded"}


@app.get("/api/equity-snapshots/{profile}")
def get_equity_history(profile: DatabaseKind) -> dict[str, object]:
    return {"profile": profile, "snapshots": list_equity_snapshots(profile)}
