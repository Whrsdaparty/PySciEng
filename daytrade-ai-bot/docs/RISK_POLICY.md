# Risk Policy

This project is designed around calculated risk, not reckless risk. The goal is to give the trader a clear plan, visible assumptions, explicit failure limits, and a repeatable research process.

## Operating principle

Scared money does not make money, but unmanaged money disappears. The bot should help convert emotion into measured exposure.

## Hard safety boundaries

The first production-grade version should enforce:

- Human review before every real trade.
- No autonomous live order placement in version 0.1.
- Maximum daily account loss.
- Maximum single-position loss.
- Maximum trade count per day.
- Maximum percentage of capital in high-risk trades.
- Kill switch after loss limit breach.
- No trading during missing-data or stale-data conditions.
- No secrets committed to GitHub.

## Suggested default risk limits

| Control | Starting value |
|---|---:|
| Max daily loss | 2% of account or less |
| Max loss per low-risk position | 0.5% |
| Max loss per medium-risk position | 1.0% |
| Max loss per high-risk position | 2.0% |
| Max high-risk capital allocation | 30% until proven otherwise |
| Required paper-trading validation | 30-90 trading days |

## Research profile

The research profile should use fake funds. Its purpose is to test strategy viability, collect logs, and identify failure modes without financial damage.

Required logs:

- Date and time of generated plan
- Symbols considered
- Data sources used
- Strategy signals used
- Rejected trade reasons
- Hypothetical entries/exits
- Simulated P/L
- Maximum drawdown
- Win rate
- Average win/loss ratio
- Notes and manual observations

## Live-tracking profile

The live-tracking profile should track real positions but should not execute trades in early versions.

Track:

- Symbol
- Share count
- Starting price
- Current price
- Cost basis
- Unrealized P/L
- Realized P/L
- Risk bucket
- Reason for trade
- Exit rule
- Stop-loss rule

## Promotion rule from paper to real

A strategy should not be considered for real trading until it has survived:

1. A minimum sample size of trades.
2. Losing streaks.
3. High-volatility days.
4. Low-volume/noisy days.
5. Out-of-sample testing.
6. Slippage and commission assumptions.
7. A maximum drawdown review.

## Final rule

No single trade should be capable of destroying the account. Survival is a strategy feature.
