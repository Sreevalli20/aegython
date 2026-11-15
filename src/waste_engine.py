"""Waste prevention intelligence: daily action plan derived from real data."""

from __future__ import annotations

from . import analytics_engine, expiry_engine, inventory, recommendation_engine


def build_daily_plan(db_path=None, assessed: list[dict] | None = None,
                     meals: dict | None = None) -> dict:
    """Assemble an actionable, traceable daily food-saving plan.

    Every recommendation is grounded in an actual inventory record or a
    computed expiry assessment — nothing is fabricated.
    """
    if assessed is None:
        assessed = expiry_engine.assess_inventory(db_path=db_path)
    if meals is None:
        items = inventory.list_items(db_path=db_path, status="active")
        meals = recommendation_engine.recommend_meals(items=items, top_k=5,
                                                      db_path=db_path)

    expiring = [a for a in assessed
                if a["urgency"] in ("expired", "critical", "high")]
    restock = _restock(db_path)
    top_meals = meals.get("recommendations", [])[:3]

    actions = []
    for a in expiring[:6]:
        actions.append({
            "priority": "high" if a["urgency"] in ("expired", "critical") else "medium",
            "type": "expiry",
            "text": f"{a['name']} ({a['quantity']} {a['unit']}, {a['location']}): "
                    f"{a['action']}",
            "item_id": a["item_id"],
            "days_remaining": a["days_remaining"],
        })
    for m in top_meals:
        actions.append({
            "priority": "medium",
            "type": "meal",
            "text": f"Cook '{m['recipe']}' — {m['match_pct']}% of ingredients already "
                    f"in your kitchen (prep ~{m.get('prep_time_min') or '?'} min).",
            "recipe": m["recipe"],
        })
    for r in restock[:3]:
        if not r["already_listed"]:
            actions.append({
                "priority": "low",
                "type": "restock",
                "text": r["reason"] + " Consider adding it to your shopping list.",
                "item_id": r["item"]["id"],
            })

    return {
        "generated_for": "today",
        "expiry_items": expiring,
        "top_meals": top_meals,
        "restock": restock,
        "actions": actions,
        "stats": {
            "expiring_count": len(expiring),
            "active_items": len(assessed),
            "meal_options": len(top_meals),
        },
        "avoid_buying": _avoid_buying(db_path),
    }


def _restock(db_path):
    from . import shopping_engine
    return shopping_engine.restock_suggestions(db_path=db_path)


def _avoid_buying(db_path) -> list[str]:
    """Ingredients the household already has plenty of — don't rebuy."""
    items = inventory.list_items(db_path=db_path, status="active")
    plentiful = []
    for it in items:
        threshold = it.get("min_threshold") or 0
        if it["quantity"] > max(threshold * 2, threshold + 1):
            plentiful.append(f"{it['name']} ({it['quantity']} {it['unit']} in stock)")
    return sorted(plentiful)[:8]


def waste_risk_score(assessed: list[dict], db_path=None) -> dict:
    """Simple transparent waste-risk estimate for the dashboard.

    Score = weighted count of items by urgency. It is an estimate of exposure,
    not a prediction of actual waste.
    """
    weights = {"expired": 4, "critical": 3, "high": 2, "medium": 1}
    score = sum(weights.get(a["urgency"], 0) for a in assessed)
    exp_summary = analytics_engine.expiry_summary(db_path=db_path)
    return {
        "score": score,
        "level": "high" if score >= 8 else "medium" if score >= 3 else "low",
        "basis": "Weighted count of expired/expiring items (expired=4, critical=3, high=2, medium=1).",
        "expired_items_logged": exp_summary.get("wasted_events", 0),
        "estimated_waste_value": exp_summary.get("wasted_value", 0.0),
    }
