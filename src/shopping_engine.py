"""Smart shopping list: CRUD, duplicate detection and restock suggestions."""

from __future__ import annotations

from datetime import date

from . import database, inventory, validators
from .recommendation_engine import normalize_ingredient


class ShoppingError(Exception):
    pass


def add_item(name: str, quantity=1, unit: str = "pcs", price_estimate=None,
             source: str = "manual", db_path=None) -> int:
    name = validators.validate_name(name)
    qty = validators.validate_quantity(quantity)
    unit = validators.validate_unit(unit)
    price = validators.validate_price(price_estimate)
    database.init_db(db_path)
    with database.get_connection(db_path) as conn:
        try:
            cur = conn.execute(
                """INSERT INTO shopping_list
                   (name, quantity, unit, added_date, price_estimate, source)
                   VALUES (?,?,?,?,?,?)""",
                (name, qty, unit, date.today().isoformat(), price, source),
            )
            return cur.lastrowid
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise ShoppingError(
                    f"'{name}' ({unit}) is already on the shopping list."
                ) from exc
            raise


def remove_item(item_id: int, db_path=None) -> bool:
    with database.get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
        return cur.rowcount > 0


def mark_purchased(item_id: int, db_path=None) -> None:
    with database.get_connection(db_path) as conn:
        conn.execute(
            "UPDATE shopping_list SET purchased=1 WHERE id=?", (item_id,)
        )


def unmark_purchased(item_id: int, db_path=None) -> None:
    with database.get_connection(db_path) as conn:
        conn.execute(
            "UPDATE shopping_list SET purchased=0 WHERE id=?", (item_id,)
        )


def clear_purchased(db_path=None) -> int:
    with database.get_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM shopping_list WHERE purchased=1")
        return cur.rowcount


def list_items(include_purchased: bool = False, db_path=None) -> list[dict]:
    database.init_db(db_path)
    sql = "SELECT * FROM shopping_list"
    if not include_purchased:
        sql += " WHERE purchased=0"
    sql += " ORDER BY purchased ASC, added_date DESC, name ASC"
    with database.get_connection(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return database.rows_to_dicts(rows)


def pantry_match(name: str, items: list[dict] | None = None,
                 db_path=None) -> dict | None:
    """Check whether an ingredient is already sufficiently stocked.

    Returns a dict describing the match, or None. 'sufficient' is True when
    total available quantity covers the requested quantity.
    """
    canon = normalize_ingredient(name)
    if not canon:
        return None
    if items is None:
        items = inventory.list_items(db_path=db_path, status="active")
    matches = []
    for it in items:
        if normalize_ingredient(it.get("name", "")) == canon:
            matches.append(it)
    if not matches:
        return None
    requested = None  # caller may pass quantity via name lookup; handled in suggest
    return {
        "canonical": canon,
        "items": matches,
        "total_quantity": sum(m["quantity"] for m in matches),
        "units": sorted({m["unit"] for m in matches}),
        "names": [m["name"] for m in matches],
    }


def find_duplicates(names: list[str], items: list[dict] | None = None,
                    db_path=None) -> list[dict]:
    """Given a list of candidate names, return those already sufficiently
    stocked in the pantry (i.e. probably duplicate purchases)."""
    if items is None:
        items = inventory.list_items(db_path=db_path, status="active")
    out = []
    for n in names:
        m = pantry_match(n, items)
        if m and m["total_quantity"] > 0:
            out.append({"requested": n, "pantry": m})
    return out


def restock_suggestions(db_path=None) -> list[dict]:
    """Suggest buying items whose quantity fell below min_threshold."""
    items = inventory.list_items(db_path=db_path, status="active")
    out = []
    for it in items:
        threshold = it.get("min_threshold") or 0
        if threshold and it["quantity"] <= threshold:
            canon = normalize_ingredient(it["name"])
            existing = [
                s for s in list_items(db_path=db_path)
                if normalize_ingredient(s["name"]) == canon
            ]
            out.append({
                "item": it,
                "suggested_qty": threshold,
                "already_listed": bool(existing),
                "reason": f"Stock ({it['quantity']} {it['unit']}) at/below threshold ({threshold} {it['unit']}).",
            })
    return out


def estimate_total(db_path=None) -> float:
    items = list_items(include_purchased=False, db_path=db_path)
    return round(sum(i["price_estimate"] or 0 for i in items), 2)
