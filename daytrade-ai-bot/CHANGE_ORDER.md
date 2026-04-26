# CHANGE ORDER

Single-file revision and change order log for the Daytrade AI Bot project.

## Versioning convention

- `0.x` = planning, scaffold, prototypes, research/paper-trading only.
- `1.x` = stable local research application.
- `2.x` = broker-connected read-only tracking.
- `3.x` = live order staging with human confirmation.
- Autonomous live trading is explicitly out of scope until the system passes risk, audit, and validation gates.

---

## v0.1.0 - Initial Python scaffold

**Status:** Committed

**Summary:** Created the first Python-first project scaffold under `Whrsdaparty/PySciEng/daytrade-ai-bot/`.

**Added:**

- `README.md`
- `pyproject.toml`
- `.env.example`
- `src/daytrade_ai_bot/__init__.py`
- `src/daytrade_ai_bot/models.py`
- `src/daytrade_ai_bot/risk_allocator.py`
- `src/daytrade_ai_bot/reports/daily_report.py`
- `src/daytrade_ai_bot/scheduling/morning_report.py`
- `tests/test_risk_allocator.py`
- `docs/RISK_POLICY.md`
- `docs/DATA_SOURCES.md`

**Core decisions:**

- Use Python as the main implementation language.
- Use FastAPI for the backend.
- Use research/paper trading before live trading.
- Keep live broker execution disabled in early versions.
- Require human review before any real trade.
- Track low, medium, and high risk buckets.
- Normalize risk bucket values to total 100%.
- Track user-facing risk knobs and a fine-adjustment value.
- Build toward a 5:20 AM daily strategy report.

**Risk posture:**

- Aggressive strategy exploration is acceptable in research mode.
- Real capital must be protected by max-loss rules, position-size rules, and kill-switch behavior.
- No API keys or brokerage credentials are committed.

---

## v0.2.0 - Bootstrap web allocation form

**Status:** Committed

**Summary:** Converted the initial interaction concept from CLI-first to a local web form using Bootstrap, custom CSS, JavaScript, and the existing Python risk allocator.

**Added:**

- `src/daytrade_ai_bot/web/app.py`
- `src/daytrade_ai_bot/web/templates/index.html`
- `src/daytrade_ai_bot/web/static/css/styles.css`
- `src/daytrade_ai_bot/web/static/js/app.js`
- `CHANGE_ORDER.md`

**Behavior:**

- Local Bootstrap form accepts daily trading capital.
- Sliders control low, medium, and high risk values from 0 to 100.
- Fine adjustment tilts allocation slightly toward or away from high risk.
- JavaScript shows live normalized percentages and dollar allocations.
- Form submits to `/api/allocate`.
- FastAPI endpoint uses the Python risk allocator as the source of truth.
- API response displays the Python-backed allocation result.

---

## v0.2.1 - Change tracking terminology update

**Status:** Committed

**Summary:** Renamed the single revision-tracking file from `CHANGEOVER.md` to `CHANGE_ORDER.md` and changed terminology from changeover to change order.

---

## v0.2.2 - Daily report jargon notes and aesthetic UI polish

**Status:** Committed

**Summary:** Added sourced investment jargon notes for the daily report learning layer and polished the web UI to look more like a clean trading dashboard.

**Added/changed:**

- `src/daytrade_ai_bot/web/static/data/jargon_notes.json`
- Bootstrap modal for investment jargon notes.
- JavaScript loader for sourced jargon notes.
- More refined CSS: dark hero header, softer cards, polished controls, dashboard-style allocation cards, and modal note cards.

**Source direction:**

- Use investor-education sources such as SEC Investor.gov and FINRA for jargon notes.
- Avoid unsourced trading-influencer terminology.

---

## v0.3.0 - Separate simulation and real-investing databases

**Status:** Committed

**Summary:** Added physically separate SQLite databases for simulation and real-investing history.

**Added:**

- `src/daytrade_ai_bot/storage.py`

**Database files created locally at runtime:**

- `data/simulation_trading.sqlite3`
- `data/real_investing.sqlite3`

**Tables:**

- `trades`
- `positions`
- `realized_gains`
- `equity_snapshots`

**FastAPI endpoints added:**

- `POST /api/trades`
- `GET /api/trades/{profile}` where `profile` is `simulation` or `real`
- `POST /api/equity-snapshots`
- `GET /api/equity-snapshots/{profile}` where `profile` is `simulation` or `real`

**Behavior:**

- Simulation trades and real trades are not stored in the same database.
- Trade history can be retrieved separately for each profile.
- Equity snapshots can track cash, open position value, realized gains, unrealized gains, and account value over time.

---

## v0.4.0 - Trade history and gains tracking web UI

**Status:** Committed

**Summary:** Added web dashboard screens for recording trades, viewing trade history, saving equity snapshots, and viewing gains history by active database.

**Changed:**

- `src/daytrade_ai_bot/web/templates/index.html`
- `src/daytrade_ai_bot/web/static/js/app.js`
- `src/daytrade_ai_bot/web/static/css/styles.css`
- `CHANGE_ORDER.md`

**Added UI features:**

- Active database selector: `Simulation / research` or `Real investing`.
- Tabbed dashboard: Daily Plan, Trades, Gains, Learning Notes.
- Trade-entry form.
- Trade-history table filtered by selected database.
- Equity snapshot form.
- Gain summary cards for latest account value, realized gains, and unrealized gains.
- Equity/gains history table filtered by selected database.

**Behavior:**

- Trade records are sent to `POST /api/trades`.
- Trade history loads from `GET /api/trades/{profile}`.
- Equity snapshots are sent to `POST /api/equity-snapshots`.
- Equity history loads from `GET /api/equity-snapshots/{profile}`.
- Switching the active database refreshes both trade history and gain history.

---

## Current run target

```bash
cd daytrade-ai-bot
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn daytrade_ai_bot.web.app:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

---

## Next planned version - v0.5.0

**Goal:** Add true position accounting and visual charts.

**Planned additions:**

- Automatically update positions from buy/sell trades.
- Calculate realized gains from matched exits instead of manual entry only.
- Calculate unrealized gains from current price marks.
- Add basic gains chart.
- Saved daily reports.
- Audit log entries for every generated strategy allocation.

