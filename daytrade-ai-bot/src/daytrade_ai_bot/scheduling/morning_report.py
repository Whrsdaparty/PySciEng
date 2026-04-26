from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler


def configure_morning_report_scheduler(timezone: str = "America/New_York") -> BackgroundScheduler:
    """Create a scheduler configured for the 5:20 AM report job.

    The actual report job will be attached once email/report delivery is implemented.
    """

    scheduler = BackgroundScheduler(timezone=timezone)
    return scheduler


def add_daily_report_job(scheduler: BackgroundScheduler, job_func) -> None:
    scheduler.add_job(
        job_func,
        trigger="cron",
        hour=5,
        minute=20,
        id="daily_strategy_report_0520",
        replace_existing=True,
    )
