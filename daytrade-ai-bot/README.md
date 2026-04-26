# Daytrade AI Bot

Python-first scaffold for a day-trading strategy assistant with paper-trading research mode, live-tracking mode, risk buckets, explainable strategy reports, and morning report scheduling.

## Current scope

This first version is intentionally conservative:

- Generates strategy reports and simulated trade plans.
- Supports research/paper trading with fake funds.
- Supports a live-tracking profile for positions, starting price, shares, and realized/unrealized P/L.
- Does **not** place autonomous live orders.
- Keeps broker execution behind a future human-review gate.
- Separates strategy logic, risk allocation, portfolio tracking, market-data adapters, report generation, and UI/API layers.

## Core user requirements captured

- Daily funds split into low, medium, and high risk pools.
- Risk sliders/knobs from 0 to 100 percent.
- Auto-normalization so low + medium + high = 100 percent.
- Fine adjustment control for small allocation changes.
- Target-goal input that scales position sizing and risk tolerance.
- Explainability layer showing which indicators, news, signals, assumptions, and constraints influenced the plan.
- Research profile using fake funds for validation.
- Real profile for tracking actual investments, including starting price, share count, current price, cost basis, and P/L.
- Daily strategy report scheduled for 5:20 AM.

## Proposed stack

- Python 3.12+
- FastAPI for backend API
- Pydantic for typed models
- SQLite first, PostgreSQL later
- APScheduler or cron for 5:20 AM reports
- Pandas/Numpy for data handling
- Optional later: Streamlit, Dash, or React frontend
- Optional later: broker adapters such as Alpaca, Schwab, Interactive Brokers, or Tradier

## Safety boundaries

This project should be treated as decision-support software, not a guaranteed-profit trading machine. The first working release should require human approval before any real trade is placed. No API keys, brokerage credentials, account numbers, or secrets should ever be committed to GitHub.

## Initial folder map

```text
daytrade-ai-bot/
  README.md
  pyproject.toml
  .env.example
  docs/
    PROJECT_BRIEF.md
    ARCHITECTURE.md
    RISK_POLICY.md
    ROADMAP.md
  src/daytrade_ai_bot/
    __init__.py
    models.py
    risk_allocator.py
    profiles.py
    explainability.py
    reports/daily_report.py
    scheduling/morning_report.py
  tests/
    test_risk_allocator.py
```

## Development start

```bash
cd daytrade-ai-bot
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Immediate next build step

Implement a minimal CLI command that:

1. Accepts daily capital and three risk knob values.
2. Normalizes low/medium/high buckets to 100 percent.
3. Creates paper-trade candidate allocations.
4. Produces a plain-text daily report.
5. Writes an audit record explaining every assumption used.
