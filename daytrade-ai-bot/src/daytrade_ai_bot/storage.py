from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

DatabaseKind = Literal["simulation", "real"]


@dataclass(frozen=True)
class DatabaseConfig:
    data_dir: Path = Path("data")
    simulation_name: str = "simulation_trading.sqlite3"
    real_name: str = "real_investing.sqlite3"

    def path_for(self, kind: DatabaseKind) -> Path:
        if kind == "simulation":
            return self.data_dir / self.simulation_name
        if kind == "real":
            return self.data_dir / self.real_name
        raise ValueError(f"Unknown database kind: {kind}")


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    trade_time TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('buy', 'sell')),
    shares TEXT NOT NULL,
    price TEXT NOT NULL,
    fees TEXT NOT NULL DEFAULT '0.00',
    risk_bucket TEXT NOT NULL CHECK(risk_bucket IN ('low', 'medium', 'high')),
    strategy_name TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    shares TEXT NOT NULL,
    average_entry_price TEXT NOT NULL,
    current_price TEXT,
    risk_bucket TEXT NOT NULL CHECK(risk_bucket IN ('low', 'medium', 'high')),
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('open', 'closed')) DEFAULT 'open',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS realized_gains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    shares_closed TEXT NOT NULL,
    entry_price TEXT NOT NULL,
    exit_price TEXT NOT NULL,
    fees TEXT NOT NULL DEFAULT '0.00',
    realized_gain TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    cash TEXT NOT NULL,
    open_position_value TEXT NOT NULL,
    realized_gain_total TEXT NOT NULL,
    unrealized_gain_total TEXT NOT NULL,
    account_value TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, trade_time);
CREATE INDEX IF NOT EXISTS idx_positions_symbol_status ON positions(symbol, status);
CREATE INDEX IF NOT EXISTS idx_realized_gains_symbol ON realized_gains(symbol);
CREATE INDEX IF NOT EXISTS idx_equity_snapshots_created_at ON equity_snapshots(created_at);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_database(kind: DatabaseKind, config: DatabaseConfig | None = None) -> sqlite3.Connection:
    config = config or DatabaseConfig()
    db_path = config.path_for(kind)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(kind: DatabaseKind, config: DatabaseConfig | None = None) -> Path:
    config = config or DatabaseConfig()
    db_path = config.path_for(kind)
    with connect_database(kind, config) as connection:
        connection.executescript(SCHEMA_SQL)
    return db_path


def initialize_all_databases(config: DatabaseConfig | None = None) -> dict[DatabaseKind, Path]:
    config = config or DatabaseConfig()
    return {
        "simulation": initialize_database("simulation", config),
        "real": initialize_database("real", config),
    }


def record_trade(
    *,
    kind: DatabaseKind,
    symbol: str,
    side: Literal["buy", "sell"],
    shares: Decimal,
    price: Decimal,
    risk_bucket: Literal["low", "medium", "high"],
    trade_time: datetime | None = None,
    fees: Decimal = Decimal("0.00"),
    strategy_name: str = "",
    notes: str = "",
    config: DatabaseConfig | None = None,
) -> int:
    initialize_database(kind, config)
    now = utc_now_iso()
    trade_time_iso = (trade_time or datetime.now(timezone.utc)).isoformat()

    with connect_database(kind, config) as connection:
        cursor = connection.execute(
            """
            INSERT INTO trades (
                created_at, trade_time, symbol, side, shares, price, fees,
                risk_bucket, strategy_name, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                trade_time_iso,
                symbol.upper(),
                side,
                str(shares),
                str(price),
                str(fees),
                risk_bucket,
                strategy_name,
                notes,
            ),
        )
        return int(cursor.lastrowid)


def list_trades(kind: DatabaseKind, config: DatabaseConfig | None = None) -> list[dict[str, object]]:
    initialize_database(kind, config)
    with connect_database(kind, config) as connection:
        rows = connection.execute(
            "SELECT * FROM trades ORDER BY trade_time DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def record_equity_snapshot(
    *,
    kind: DatabaseKind,
    cash: Decimal,
    open_position_value: Decimal,
    realized_gain_total: Decimal,
    unrealized_gain_total: Decimal,
    notes: str = "",
    config: DatabaseConfig | None = None,
) -> int:
    initialize_database(kind, config)
    account_value = cash + open_position_value
    with connect_database(kind, config) as connection:
        cursor = connection.execute(
            """
            INSERT INTO equity_snapshots (
                created_at, cash, open_position_value, realized_gain_total,
                unrealized_gain_total, account_value, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now_iso(),
                str(cash),
                str(open_position_value),
                str(realized_gain_total),
                str(unrealized_gain_total),
                str(account_value),
                notes,
            ),
        )
        return int(cursor.lastrowid)


def list_equity_snapshots(kind: DatabaseKind, config: DatabaseConfig | None = None) -> list[dict[str, object]]:
    initialize_database(kind, config)
    with connect_database(kind, config) as connection:
        rows = connection.execute(
            "SELECT * FROM equity_snapshots ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]
