"""Food waste analytics: trends, totals and estimates from recorded events.

All figures derived from consumption_log are RECORDINGS of user actions.
Anything labelled 'estimated' is a model estimate (quantity x unit price) —
never presented as verified savings.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import database


def _period_start(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def consumption_summary(db_path=None, days: int | None = None) -> dict:
    database.init_db(db_path)
    sql = "SELECT * FROM consumption_log"
    params: list = []
    if days is not None:
        sql += " WHERE event_date >= ?"
        params.append(_period_start(days))
    with database.get_connection(db_path) as conn:
        rows = database.rows_to_dicts(conn.execute(sql, params).fetchall())

    consumed = [r for r in rows if r["event"] == "consumed"]
    wasted = [r for r in rows if r["event"] in ("wasted", "discarded")]
    return {
        "events": len(rows),
        "consumed_events": len(consumed),
        "wasted_events": len(wasted),
        "consumed_qty": round(sum(r["quantity"] for r in consumed), 2),
        "wasted_qty": round(sum(r["quantity"] for r in wasted), 2),
        "consumed_value": round(sum(r["est_value"] or 0 for r in consumed), 2),
        "wasted_value": round(sum(r["est_value"] or 0 for r in wasted), 2),
        "records": rows,
    }


def expiry_summary(db_path=None) -> dict:
    s = consumption_summary(db_path=db_path)
    return {
        "wasted_events": s["wasted_events"],
        "wasted_value": s["wasted_value"],
        "wasted_qty": s["wasted_qty"],
    }


def top_wasted(db_path=None, limit: int = 8) -> list[dict]:
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        rows = database.rows_to_dicts(conn.execute(
            """SELECT item_name, category, COUNT(*) AS times,
                      SUM(quantity) AS qty, SUM(est_value) AS value
               FROM consumption_log
               WHERE event IN ('wasted','discarded')
               GROUP BY lower(item_name)
               ORDER BY times DESC, value DESC NULLS LAST
               LIMIT ?""",
            (limit,),
        ).fetchall())
    for r in rows:
        r["value"] = round(r["value"] or 0, 2)
        r["qty"] = round(r["qty"], 2)
    return rows


def category_breakdown(db_path=None) -> list[dict]:
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        rows = database.rows_to_dicts(conn.execute(
            """SELECT category,
                      SUM(CASE WHEN event='consumed' THEN quantity ELSE 0 END) AS consumed_qty,
                      SUM(CASE WHEN event IN ('wasted','discarded') THEN quantity ELSE 0 END) AS wasted_qty,
                      SUM(CASE WHEN event IN ('wasted','discarded') THEN est_value ELSE 0 END) AS wasted_value
               FROM consumption_log GROUP BY category"""
        ).fetchall())
    for r in rows:
        r["wasted_value"] = round(r["wasted_value"] or 0, 2)
        r["consumed_qty"] = round(r["consumed_qty"], 2)
        r["wasted_qty"] = round(r["wasted_qty"], 2)
    return rows


def daily_series(db_path=None, days: int = 30) -> list[dict]:
    """Per-day consumed/wasted quantities for trend charts."""
    database.init_db(db_path)
    start = _period_start(days)
    with database.get_connection(db_path) as conn:
        rows = database.rows_to_dicts(conn.execute(
            """SELECT event_date,
                      SUM(CASE WHEN event='consumed' THEN quantity ELSE 0 END) AS consumed,
                      SUM(CASE WHEN event IN ('wasted','discarded') THEN quantity ELSE 0 END) AS wasted
               FROM consumption_log
               WHERE event_date >= ?
               GROUP BY event_date ORDER BY event_date""",
            (start,),
        ).fetchall())
    return [{"date": r["event_date"], "consumed": r["consumed"] or 0,
             "wasted": r["wasted"] or 0} for r in rows]


def weekly_series(db_path=None, weeks: int = 12) -> list[dict]:
    """ISO-week aggregation for longer trends."""
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        rows = database.rows_to_dicts(conn.execute(
            """SELECT strftime('%Y-W%W', event_date) AS week,
                      SUM(CASE WHEN event='consumed' THEN quantity ELSE 0 END) AS consumed,
                      SUM(CASE WHEN event IN ('wasted','discarded') THEN quantity ELSE 0 END) AS wasted,
                      SUM(CASE WHEN event IN ('wasted','discarded') THEN est_value ELSE 0 END) AS wasted_value
               FROM consumption_log GROUP BY week ORDER BY week"""
        ).fetchall())
    for r in rows:
        r["wasted_value"] = round(r["wasted_value"] or 0, 2)
    return rows[-weeks:]


def inventory_value(db_path=None) -> float:
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT SUM(price) AS v FROM items WHERE status='active'"
        ).fetchone()
    return round(row["v"] or 0, 2)
