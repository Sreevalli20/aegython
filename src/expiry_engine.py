"""Expiry intelligence engine.

Transparent, explainable rules — no black-box scoring. For every item we
compute days remaining and assign an urgency level with written reasoning.

IMPORTANT: an expiry date is a label printed by the manufacturer or entered
by the user. This engine NEVER declares food safe or unsafe; it surfaces
label dates and recommends sensible next actions. For 'use_by' items we
always defer to the label.
"""

from __future__ import annotations

from datetime import date

from . import inventory

URGENCY_ORDER = {"expired": 0, "critical": 1, "high": 2, "medium": 3, "ok": 4, "none": 5}

URGENCY_META = {
    "expired": {"label": "Expired", "color": "#B3261E", "icon": "!"},
    "critical": {"label": "Use today", "color": "#C0392B", "icon": "!"},
    "high": {"label": "Expiring soon", "color": "#D35400", "icon": "~"},
    "medium": {"label": "Plan to use", "color": "#B8860B", "icon": "~"},
    "ok": {"label": "Fresh", "color": "#1B7A43", "icon": "+"},
    "none": {"label": "No date", "color": "#6B7280", "icon": "?"},
}


def days_remaining(expiry_date: str | None, today: date | None = None) -> int | None:
    if not expiry_date:
        return None
    today = today or date.today()
    try:
        exp = date.fromisoformat(expiry_date)
    except ValueError:
        return None
    return (exp - today).days


def classify_item(item: dict, today: date | None = None) -> dict:
    """Return an explainable urgency assessment for one inventory item."""
    today = today or date.today()
    days = days_remaining(item.get("expiry_date"), today)
    date_type = item.get("date_type", "user")
    label = {
        "best_before": "best-before (quality) date",
        "use_by": "use-by (safety) date",
        "user": "user-entered date",
    }.get(date_type, "date")

    base = {
        "item_id": item.get("id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "quantity": item.get("quantity"),
        "unit": item.get("unit"),
        "location": item.get("location"),
        "expiry_date": item.get("expiry_date"),
        "purchase_date": item.get("purchase_date"),
        "date_type": date_type,
        "days_remaining": days,
        "date_label": label,
    }

    if days is None:
        base.update(
            urgency="none",
            reasons=["No expiry date recorded — expiry risk cannot be estimated."],
            action="Add an expiry date (check the package label) to enable tracking.",
        )
        return base

    if days < 0:
        overdue = -days
        reasons = [
            f"{overdue} day(s) past the {label}.",
            "Food past its date may be unsafe — this engine does not judge safety.",
        ]
        if date_type == "use_by":
            reasons.append("This is a use-by date: follow the package label and local food-safety guidance.")
            action = "Check the label. If past a use-by date, do not eat it — discard it safely."
        else:
            action = "Check the label. Past best-before usually means quality loss, not automatic danger — inspect before deciding."
        base.update(urgency="expired", reasons=reasons, action=action)
        return base

    if days <= 1:
        base.update(
            urgency="critical",
            reasons=[
                f"Only {days} day(s) until the {label}.",
                "Very short window to use or preserve this item.",
            ],
            action=(
                "Use today, or freeze/preserve it now. If it carries a use-by date, follow the label exactly."
            ),
        )
        return base

    if days <= 3:
        base.update(
            urgency="high",
            reasons=[
                f"{days} days until the {label}.",
                "Needs to be cooked or preserved within the next few days.",
            ],
            action="Cook it within 2-3 days, or freeze it. Check Discover Meals for recipes using this item.",
        )
        return base

    if days <= 7:
        base.update(
            urgency="medium",
            reasons=[
                f"{days} days until the {label}.",
                "Plan a meal around this item this week.",
            ],
            action="Schedule a meal this week that uses this ingredient before it expires.",
        )
        return base

    base.update(
        urgency="ok",
        reasons=[f"{days} days remaining until the {label} — no immediate action needed."],
        action="No urgent action. Keep stored correctly.",
    )
    return base


def assess_inventory(items: list[dict] | None = None, today: date | None = None,
                     db_path=None) -> list[dict]:
    """Classify every active item and return them sorted by urgency."""
    if items is None:
        items = inventory.list_items(db_path=db_path, status="active")
    assessed = [classify_item(i, today) for i in items]
    assessed.sort(key=lambda a: (URGENCY_ORDER.get(a["urgency"], 9),
                                 a["days_remaining"] if a["days_remaining"] is not None else 9999))
    return assessed


def summary(assessed: list[dict]) -> dict:
    counts = {k: 0 for k in URGENCY_META}
    for a in assessed:
        counts[a["urgency"]] = counts.get(a["urgency"], 0) + 1
    return {
        "total": len(assessed),
        "expired": counts.get("expired", 0),
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "ok": counts.get("ok", 0),
        "none": counts.get("none", 0),
        "needs_attention": counts.get("expired", 0) + counts.get("critical", 0) + counts.get("high", 0),
    }
