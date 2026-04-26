from __future__ import annotations

from daytrade_ai_bot.models import StrategyReport


def render_daily_report(report: StrategyReport) -> str:
    lines: list[str] = []
    lines.append(f"Daily Trading Strategy Report - {report.plan.trading_date.isoformat()}")
    lines.append(f"Profile: {report.profile_name}")
    lines.append(f"Created: {report.created_at.isoformat()}")
    lines.append("")
    lines.append("Capital Plan")
    lines.append(f"Starting cash: ${report.plan.starting_cash}")
    lines.append(f"Target daily return: {report.plan.target_daily_return_percent:.2f}%")
    lines.append(f"Maximum daily loss: {report.plan.max_daily_loss_percent:.2f}%")
    lines.append("")
    lines.append("Risk Buckets")
    for allocation in report.plan.allocations:
        lines.append(
            f"- {allocation.bucket.value}: {allocation.percent:.2f}% | "
            f"${allocation.dollars} | bucket max loss {allocation.max_loss_percent:.2f}%"
        )
    lines.append("")
    lines.append("Insights Used")
    if report.insights:
        for insight in report.insights:
            lines.append(
                f"- [{insight.category}] {insight.source}: "
                f"{insight.summary} | confidence={insight.confidence:.2f}"
            )
    else:
        lines.append("- No market insights attached yet. Use paper mode until data adapters are configured.")
    lines.append("")
    lines.append("Warnings")
    for warning in report.warnings or ["Human review required before any real trade."]:
        lines.append(f"- {warning}")
    lines.append("")
    lines.append(f"Human review required: {report.human_review_required}")
    return "\n".join(lines)
