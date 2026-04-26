# CHANGEOVER

Single-file revision and change tracking log for the Daytrade AI Bot project.

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
- `CHANGEOVER.md`

**Behavior:**

- Local Bootstrap form accepts daily trading capital.
- Sliders control low, medium, and high risk values from 0 to 100.
- Fine adjustment tilts allocation slightly toward or away from high risk.
- JavaScript shows live normalized percentages and dollar allocations.
- Form submits to `/api/allocate`.
- FastAPI endpoint uses the Python risk allocator as the source of truth.
- API response displays the Python-backed allocation result.

**Run target:**

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

## Next planned version - v0.3.0

**Goal:** Add profile support and persistent storage.

**Planned additions:**

- Research profile form.
- Live-tracking profile form.
- SQLite database layer.
- Position entry fields: symbol, shares, starting price, current price, risk bucket, notes.
- Saved daily reports.
- Audit log entries for every generated strategy allocation.

