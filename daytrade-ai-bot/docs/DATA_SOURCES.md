# Market Data Sources

This project should use a pluggable market-data layer. Free sources are useful for research, backtesting, education, and paper trading, but they usually have limitations: delayed quotes, rate limits, restricted historical depth, no official redistribution rights, or weak reliability for real-time trading.

## Data categories needed

1. Daily OHLCV bars
2. Intraday OHLCV bars
3. Real-time or near-real-time quotes
4. Fundamental data
5. News and sentiment data
6. Corporate actions
7. Economic calendar data
8. Optional: options chains and implied volatility

## Free or freemium sources to evaluate

| Source | Best use | Notes |
|---|---|---|
| Yahoo Finance via `yfinance` | Daily/intraday research and prototyping | Convenient, unofficial, can break, not ideal for production trading. |
| Alpha Vantage | Stocks, forex, crypto, indicators | Free tier exists but has tight rate limits. Good for early experiments. |
| Stooq | Historical daily data | Simple free historical data for many symbols. Less suited for live trading. |
| Nasdaq Data Link | Some free datasets | Dataset availability varies. Useful for fundamentals and macro research. |
| Alpaca Market Data | Paper-trading-friendly equities/crypto data | Good candidate if using Alpaca for simulated or live brokerage integration. Data tier limitations apply. |
| Polygon.io | High-quality market data | Usually paid for serious intraday use, but may offer limited free/dev access. |
| Finnhub | Quotes, fundamentals, news | Free tier exists with limits. Good for prototype sentiment/news features. |
| FRED | Macroeconomic data | Free, reliable macroeconomic time series from the Federal Reserve Bank of St. Louis. |
| SEC EDGAR | Company filings | Free official source for filings, 10-K, 10-Q, 8-K, and insider forms. |

## Recommended first-pass data strategy

### Phase 1: Research mode

Use free/delayed data only:

- `yfinance` for prototype OHLCV bars.
- FRED for macro context.
- SEC EDGAR for filings metadata.
- Optional Alpha Vantage or Finnhub for limited news/indicator testing.

### Phase 2: Paper trading

Use a broker-compatible paper trading provider:

- Alpaca paper trading is a strong first candidate.
- Keep market-data adapter separate from broker-execution adapter.
- Store every quote, signal, generated plan, and simulated order in an audit log.

### Phase 3: Live tracking

Track real positions manually or through broker API read-only access first.

Live order placement should remain disabled until:

- Risk limits are tested.
- Paper results survive out-of-sample validation.
- Kill-switch behavior is implemented.
- Max daily loss, max position size, and max trade count are enforced.
- Human approval is required for every live order.

## Adapter interface goal

Each data provider should implement the same interface:

```python
class MarketDataProvider:
    def get_daily_bars(self, symbol: str, lookback_days: int): ...
    def get_intraday_bars(self, symbol: str, interval: str, lookback_days: int): ...
    def get_quote(self, symbol: str): ...
    def get_news(self, symbol: str, lookback_days: int): ...
```

The strategy engine should not know whether data came from Yahoo, Alpaca, Finnhub, or another provider.

## Do not commit secrets

API keys belong in environment variables or local secret storage only.

Expected `.env` entries:

```text
ALPACA_API_KEY=
ALPACA_API_SECRET=
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=
POLYGON_API_KEY=
```
