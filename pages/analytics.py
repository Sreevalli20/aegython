"""Analytics — recorded consumption/waste trends and estimates."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from src import analytics_engine, expiry_engine, inventory


def render(db_path=None) -> None:
    ui.page_header(
        "Food Waste Analytics",
        "Recorded events are facts you logged. Anything marked 'estimated' is a "
        "quantity × unit-price estimate — not verified savings.",
    )

    summary = analytics_engine.consumption_summary(db_path=db_path)
    inv_value = analytics_engine.inventory_value(db_path=db_path)
    assessed = expiry_engine.assess_inventory(db_path=db_path)
    esum = expiry_engine.summary(assessed)

    if summary["events"] == 0:
        ui.empty_state(
            "📊", "No activity recorded yet",
            "Mark items as consumed or wasted in My Pantry / Expiry Intelligence "
            "to start building your waste analytics.",
        )
    else:
        ui.metric_cards([
            {"value": summary["events"], "label": "Total events"},
            {"value": summary["consumed_events"], "label": "Consumed",
             "delta": f"{summary['consumed_qty']:.1f} qty", "delta_kind": "good"},
            {"value": summary["wasted_events"], "label": "Wasted / discarded",
             "delta_kind": "bad" if summary["wasted_events"] else "good"},
            {"value": ui.fmt_money(summary["wasted_value"]),
             "label": "Est. wasted value",
             "delta": "estimate", "delta_kind": "bad" if summary["wasted_value"] else "good"},
            {"value": ui.fmt_money(inv_value), "label": "Est. inventory value"},
            {"value": esum["needs_attention"], "label": "Items needing attention now"},
        ])

        left, right = st.columns(2)
        with left:
            ui.section_label("Daily consumption vs waste (last 30 days)")
            daily = analytics_engine.daily_series(db_path=db_path, days=30)
            if daily:
                charts.daily_waste_trend(daily, key="an_daily")
            else:
                ui.note("Not enough dated events yet.", "info")
        with right:
            ui.section_label("Estimated waste value by week")
            weekly = analytics_engine.weekly_series(db_path=db_path)
            if weekly:
                charts.weekly_waste_value(weekly, key="an_weekly")
            else:
                ui.note("No waste events recorded yet.", "info")

        ui.section_label("Waste by category")
        cats = analytics_engine.category_breakdown(db_path=db_path)
        if any(c["wasted_qty"] > 0 for c in cats):
            charts.category_waste_chart(cats, key="an_cats")
            st.dataframe(pd.DataFrame([{
                "Category": c["category"],
                "Consumed qty": c["consumed_qty"],
                "Wasted qty": c["wasted_qty"],
                "Est. wasted value": ui.fmt_money(c["wasted_value"]),
            } for c in cats]), width="stretch", hide_index=True)
        else:
            ui.note("No waste recorded by category yet — keep logging to see patterns.", "info")

        ui.section_label("Most frequently wasted ingredients")
        top = analytics_engine.top_wasted(db_path=db_path)
        if top:
            st.dataframe(pd.DataFrame([{
                "Ingredient": t["item_name"], "Category": t["category"],
                "Times wasted": t["times"], "Total qty": t["qty"],
                "Est. value": ui.fmt_money(t["value"]),
            } for t in top]), width="stretch", hide_index=True)
        else:
            ui.note("Nothing wasted yet — that's the goal. 🎉", "info")

    # Inventory composition regardless of events
    ui.section_label("Current inventory composition")
    items = inventory.list_items(db_path=db_path, status="active")
    if items:
        charts.category_inventory_chart(items, key="an_inv")
    else:
        ui.note("Inventory is empty.", "info")

    ui.note(
        "**Measurement vs estimate:** event counts and quantities are your recorded "
        "actions. Values marked 'est.' use each item's purchase price divided by "
        "quantity at the time of logging — an approximation, not an audited figure.",
        "info",
    )
