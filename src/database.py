"""SQLite persistence layer for WasteLess AI.

All household data lives in a single local SQLite database file so the app is
offline-first and does not depend on Streamlit session state.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = Path(
    os.environ.get("WASTELESS_DB_PATH", str(PROJECT_ROOT / "data" / "wasteless.db"))
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other',
    quantity REAL NOT NULL CHECK (quantity >= 0),
    unit TEXT NOT NULL DEFAULT 'pcs',
    purchase_date TEXT NOT NULL,
    expiry_date TEXT,
    date_type TEXT NOT NULL DEFAULT 'user'
        CHECK (date_type IN ('best_before', 'use_by', 'user')),
    location TEXT NOT NULL DEFAULT 'Pantry',
    price REAL CHECK (price IS NULL OR price >= 0),
    min_threshold REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'consumed', 'wasted', 'discarded')),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consumption_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other',
    quantity REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'pcs',
    event TEXT NOT NULL CHECK (event IN ('consumed', 'wasted', 'discarded')),
    event_date TEXT NOT NULL,
    est_value REAL,
    reason TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1,
    unit TEXT NOT NULL DEFAULT 'pcs',
    purchased INTEGER NOT NULL DEFAULT 0,
    added_date TEXT NOT NULL,
    price_estimate REAL,
    source TEXT NOT NULL DEFAULT 'manual',
    UNIQUE(name, unit)
);

CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_expiry ON items(expiry_date);
CREATE INDEX IF NOT EXISTS idx_log_event_date ON consumption_log(event_date);
"""


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row access by column name."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | str | None = None) -> None:
    """Create tables if they do not exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def rows_to_dicts(rows) -> list[dict]:
    return [dict(r) for r in rows]


def today_iso() -> str:
    from datetime import date

    return date.today().isoformat()


def clear_all_data(db_path: Path | str | None = None) -> None:
    """Delete every record (used by the Settings 'clear local data' action)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM consumption_log")
        conn.execute("DELETE FROM shopping_list")
