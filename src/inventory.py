"""Inventory CRUD operations backed by SQLite."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from . import database, validators


class InventoryError(Exception):
    pass


def _unit_price(item: dict) -> float | None:
    """Estimated price per unit, used for waste valuation."""
    price = item.get("price")
    qty = item.get("quantity")
    if price is None or not qty:
        return None
    return price / qty


def add_item(data: dict, db_path=None) -> int:
    """Validate and insert a new inventory item. Returns the new id."""
    name = validators.validate_name(data.get("name"))
    qty = validators.validate_quantity(data.get("quantity"))
    unit = validators.validate_unit(data.get("unit"))
    category = validators.validate_category(data.get("category"))
    location = validators.validate_location(data.get("location"))
    date_type = validators.validate_date_type(data.get("date_type"))
    purchase = validators.validate_iso_date(
        data.get("purchase_date") or date.today().isoformat(), "purchase_date"
    )
    expiry = validators.validate_iso_date(
        data.get("expiry_date"), "expiry_date", allow_none=True
    )
    if expiry and purchase and expiry < purchase:
        raise InventoryError("Expiry date cannot be before the purchase date.")
    price = validators.validate_price(data.get("price"))
    threshold = validators.validate_threshold(data.get("min_threshold"))
    notes = (data.get("notes") or "").strip()[:500]

    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO items
               (name, category, quantity, unit, purchase_date, expiry_date,
                date_type, location, price, min_threshold, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (name, category, qty, unit, purchase, expiry, date_type,
             location, price, threshold, notes),
        )
        return cur.lastrowid


def update_item(item_id: int, data: dict, db_path=None) -> None:
    existing = get_item(item_id, db_path)
    if existing is None:
        raise InventoryError(f"Item {item_id} does not exist.")
    if existing["status"] != "active":
        raise InventoryError("Only active items can be edited.")

    merged = {**existing, **{k: v for k, v in data.items() if v is not None}}
    name = validators.validate_name(merged.get("name"))
    qty = validators.validate_quantity(merged.get("quantity"))
    unit = validators.validate_unit(merged.get("unit"))
    category = validators.validate_category(merged.get("category"))
    location = validators.validate_location(merged.get("location"))
    date_type = validators.validate_date_type(merged.get("date_type"))
    purchase = validators.validate_iso_date(merged.get("purchase_date"), "purchase_date")
    expiry = validators.validate_iso_date(merged.get("expiry_date"), "expiry_date", allow_none=True)
    if expiry and purchase and expiry < purchase:
        raise InventoryError("Expiry date cannot be before the purchase date.")
    price = validators.validate_price(merged.get("price"))
    threshold = validators.validate_threshold(merged.get("min_threshold"))
    notes = (merged.get("notes") or "").strip()[:500]

    with database.get_connection(db_path) as conn:
        conn.execute(
            """UPDATE items SET name=?, category=?, quantity=?, unit=?,
               purchase_date=?, expiry_date=?, date_type=?, location=?,
               price=?, min_threshold=?, notes=?,
               updated_at=datetime('now') WHERE id=?""",
            (name, category, qty, unit, purchase, expiry, date_type, location,
             price, threshold, notes, item_id),
        )


def get_item(item_id: int, db_path=None) -> dict | None:
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return database.row_to_dict(row)


def list_items(
    db_path=None,
    status: str | None = "active",
    category: str | None = None,
    search: str | None = None,
    location: str | None = None,
    sort: str = "expiry",
) -> list[dict]:
    database.init_db(db_path)
    sql = "SELECT * FROM items WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if category and category != "All":
        sql += " AND category=?"
        params.append(category)
    if location and location != "All":
        sql += " AND location=?"
        params.append(location)
    if search:
        sql += " AND lower(name) LIKE ?"
        params.append(f"%{search.strip().lower()}%")

    order = {
        "expiry": "expiry_date IS NULL, expiry_date ASC, name ASC",
        "name": "lower(name) ASC",
        "added": "created_at DESC",
        "price": "price IS NULL, price DESC",
        "quantity": "quantity DESC",
    }.get(sort, "expiry_date IS NULL, expiry_date ASC")
    sql += f" ORDER BY {order}"

    with database.get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return database.rows_to_dicts(rows)


def delete_item(item_id: int, db_path=None) -> bool:
    """Hard-delete an item. Returns True if a row was removed."""
    with database.get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        return cur.rowcount > 0


def consume_quantity(item_id: int, qty: float, db_path=None) -> dict:
    """Reduce an item's quantity; mark consumed when it reaches zero.

    Partial consumption is logged; the remaining quantity stays active.
    Returns a summary dict for the activity feed.
    """
    item = get_item(item_id, db_path)
    if item is None:
        raise InventoryError(f"Item {item_id} does not exist.")
    if item["status"] != "active":
        raise InventoryError("Item is not active.")
    qty = validators.validate_quantity(qty)
    if qty > item["quantity"] + 1e-9:
        raise InventoryError(
            f"Cannot consume {qty} {item['unit']} — only {item['quantity']} available."
        )

    remaining = round(item["quantity"] - qty, 3)
    up = _unit_price(item)
    est_value = round(up * qty, 2) if up is not None else None

    with database.get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO consumption_log
               (item_id, item_name, category, quantity, unit, event,
                event_date, est_value, reason)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (item_id, item["name"], item["category"], qty, item["unit"],
             "consumed", date.today().isoformat(), est_value,
             "Marked as consumed via pantry"),
        )
        if remaining <= 0:
            conn.execute(
                "UPDATE items SET quantity=0, status='consumed', updated_at=datetime('now') WHERE id=?",
                (item_id,),
            )
        else:
            # Scale price with quantity so unit price stays constant.
            new_price = None
            if item.get("price") is not None:
                new_price = round(item["price"] * remaining / item["quantity"], 2)
            conn.execute(
                "UPDATE items SET quantity=?, price=COALESCE(?, price), updated_at=datetime('now') WHERE id=?",
                (remaining, new_price, item_id),
            )
    return {"item": item["name"], "quantity": qty, "unit": item["unit"],
            "remaining": remaining, "est_value": est_value}


def mark_event(item_id: int, event: str, reason: str = "", db_path=None) -> dict:
    """Mark an entire item as consumed / wasted / discarded and log it."""
    if event not in ("consumed", "wasted", "discarded"):
        raise InventoryError("event must be consumed, wasted or discarded.")
    item = get_item(item_id, db_path)
    if item is None:
        raise InventoryError(f"Item {item_id} does not exist.")
    if item["status"] != "active":
        raise InventoryError("Item is not active.")

    up = _unit_price(item)
    est_value = round(up * item["quantity"], 2) if up is not None else None
    with database.get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO consumption_log
               (item_id, item_name, category, quantity, unit, event,
                event_date, est_value, reason)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (item_id, item["name"], item["category"], item["quantity"],
             item["unit"], event, date.today().isoformat(), est_value,
             reason or f"Marked as {event}"),
        )
        conn.execute(
            "UPDATE items SET status=?, quantity=0, updated_at=datetime('now') WHERE id=?",
            ("consumed" if event == "consumed" else event, item_id),
        )
    return {"item": item["name"], "event": event, "est_value": est_value}


def recent_activity(limit: int = 10, db_path=None) -> list[dict]:
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        rows = conn.execute(
            """SELECT * FROM consumption_log
               ORDER BY event_date DESC, id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return database.rows_to_dicts(rows)


def add_sample_data(db_path=None) -> int:
    """Load the bundled sample inventory. Returns number of items added."""
    import json

    path = database.PROJECT_ROOT / "data" / "sample_inventory.json"
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    items = payload["items"] if isinstance(payload, dict) else payload
    today = date.today()
    added = 0
    for raw in items:
        data = dict(raw)
        # Resolve relative day offsets into real dates.
        for key in ("purchase_date", "expiry_date"):
            if (data.get(key) or "").startswith("offset:"):
                offset = int(data[key].split(":")[1])
                data[key] = (today + timedelta(days=offset)).isoformat()
        try:
            add_item(data, db_path)
            added += 1
        except (InventoryError, ValueError) as exc:
            print(f"Skipping invalid sample item '{data.get('name')}': {exc}")
            continue
    return added
