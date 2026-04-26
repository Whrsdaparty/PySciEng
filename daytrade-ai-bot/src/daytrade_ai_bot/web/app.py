from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from daytrade_ai_bot.models import RiskKnobs
from daytrade_ai_bot.risk_allocator import build_daily_capital_plan

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
