"""What-if simulator.

Hypothetical scenarios computed from the user's REAL current inventory.
Outputs are explicitly labelled estimates — they model exposure, not outcomes.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import expiry_engine, inventory, recommendation_engine


def simulate(db_path=None, extra_purchases: list[dict] | None = None,
             daily_extra_consumption: float = 0.0,
             waste_rate_today: float = 0.0) -> dict:
    """Run a what-if scenario against current inventory.

    extra_purchases: list of {"name", "quantity", "unit", "shelf_days"} —
        hypothetical items added to inventory for the simulation only.
    daily_extra_consumption: fraction (0-1) of active inventory assumed eaten
        per day under the scenario.
    waste_rate_today: fraction (0-1) of expiring items assumed wasted today.
    """
    items = inventory.list_items(db_path=db_path, status="active")
    assessed = expiry_engine.assess_inventory(items=items)
    today = date.today()

    baseline = expiry_engine.summary(assessed)

    # --- Scenario inventory ---
    scenario_items = [dict(i) for i in items]
    for idx, p in enumerate(extra_purchases or []):
        scenario_items.append({
            "id": -(idx + 1),  # unique negative ids so expiry matching stays correct
            "name": p.get("name", "New item"),
            "quantity": float(p.get("quantity", 1)),
            "unit": p.get("unit", "pcs"),
            "category": "Other",
            "location": "Pantry",
            "purchase_date": today.isoformat(),
            "expiry_date": (today + timedelta(days=int(p.get("shelf_days", 7)))).isoformat(),
            "date_type": "user",
            "status": "active",
            "price": p.get("price"),
            "min_threshold": 0,
        })

    scenario_assessed = expiry_engine.assess_inventory(items=scenario_items, today=today)
    scen_summary = expiry_engine.summary(scenario_assessed)

    # --- Estimated waste under scenario ---
    expiring_ids = {
        a["item_id"] for a in scenario_assessed
        if a["urgency"] in ("expired", "critical", "high")
    }
    expiring_items = [i for i in scenario_items if i["id"] in expiring_ids]
    est_waste_value = 0.0
    for it in expiring_items:
        price = it.get("price")
        if price:
            # crude estimate: item's recorded price scaled by assumed waste rate
            est_waste_value += price * waste_rate_today
    est_waste_value = round(est_waste_value, 2)

    # --- Utilization estimate ---
    total_qty = sum(i["quantity"] for i in scenario_items)
    consumed_est = total_qty * max(0.0, min(1.0, daily_extra_consumption))
    utilization = round(consumed_est / total_qty * 100, 1) if total_qty else 0.0

    # --- Meal options under scenario ---
    meals = recommendation_engine.recommend_meals(items=scenario_items, top_k=5, db_path=db_path)

    return {
        "is_estimate": True,
        "baseline": {
            "active_items": baseline["total"],
            "needs_attention": baseline["needs_attention"],
            "expired": baseline["expired"],
        },
        "scenario": {
            "active_items": scen_summary["total"],
            "needs_attention": scen_summary["needs_attention"],
            "expired": scen_summary["expired"],
            "meal_options": len(meals.get("recommendations", [])),
            "estimated_daily_utilization_pct": utilization,
            "estimated_waste_value_at_risk": est_waste_value,
        },
        "delta": {
            "attention_change": scen_summary["needs_attention"] - baseline["needs_attention"],
            "items_change": scen_summary["total"] - baseline["total"],
        },
        "disclaimer": (
            "Simulation outputs are estimates computed from your current "
            "inventory records. They illustrate directional impact only and "
            "are not predictions of actual waste or savings."
        ),
    }
