"""Home Dashboard — inventory summary, expiry alerts, plan, activity."""

from __future__ import annotations

import streamlit as st

from components import charts, ui
from src import analytics_engine, expiry_engine, inventory, waste_engine


def render(db_path=None) -> None:
    items = inventory.list_items(db_path=db_path, status="active")
    assessed = expiry_engine.assess_inventory(items=items)
    esum = expiry_engine.summary(assessed)
    plan = waste_engine.build_daily_plan(db_path=db_path, assessed=assessed)
    risk = waste_engine.waste_risk_score(assessed, db_path=db_path)
    activity = inventory.recent_activity(limit=8, db_path=db_path)
    summary = analytics_engine.consumption_summary(db_path=db_path)

    ui.page_header(
        "Home Dashboard",
        "Know what you have. Know what to use. Waste less.",
    )

    if not items:
        ui.empty_state(
            "🥬", "Your pantry is empty",
            "Add ingredients manually or load the sample household dataset to explore WasteLess AI.",
            "Load sample data", "load_sample",
        )
        if st.session_state.get("pending_action") == "load_sample":
            n = inventory.add_sample_data(db_path=db_path)
            st.session_state.pop("pending_action", None)
            st.success(f"Loaded {n} sample items.")
            st.rerun()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add your first item", use_container_width=True):
                st.session_state["nav"] = "pantry"
                st.rerun()
        return

    # --- Metric cards -------------------------------------------------------
    ui.metric_cards([
        {"value": esum["total"], "label": "Items in inventory",
         "delta": f"{esum['needs_attention']} need attention", "delta_kind": "bad" if esum["needs_attention"] else "good"},
        {"value": esum["expired"] + esum["critical"], "label": "Expired / use today",
         "delta_kind": "bad" if (esum["expired"] + esum["critical"]) else "good"},
        {"value": esum["high"] + esum["medium"], "label": "Expiring this week"},
        {"value": ui.fmt_money(analytics_engine.inventory_value(db_path=db_path)),
         "label": "Est. inventory value"},
        {"value": ui.fmt_money(summary["wasted_value"]),
         "label": "Est. value wasted (recorded)",
         "delta": f"{summary['wasted_events']} waste events", "delta_kind": "bad" if summary["wasted_value"] else "good"},
    ])

    left, right = st.columns([3, 2])

    with left:
        ui.section_label("Today's food-saving plan")
        if plan["actions"]:
            for a in plan["actions"][:6]:
                icon = {"expiry": "⚠", "meal": "🍽", "restock": "🛒"}.get(a["type"], "•")
                st.markdown(
                    f'<div class="wl-card" style="padding:12px 16px;margin-bottom:8px">'
                    f'<span style="margin-right:8px">{icon}</span>{a["text"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            ui.note("Nothing needs urgent attention — your inventory is in good shape.", "info")

        if plan["top_meals"]:
            ui.section_label("Suggested meals (ingredient-matched)")
            for m in plan["top_meals"][:3]:
                st.markdown(
                    f'<div class="wl-card" style="padding:12px 16px;margin-bottom:8px">'
                    f'<b>{m["recipe"]}</b> <span style="color:#6B7280;font-size:.82rem">'
                    f'{m["match_pct"]}% match · ~{m.get("prep_time_min") or "?"} min</span><br/>'
                    f'<span style="font-size:.85rem;color:#33413a">'
                    f'{m["reasons"][0] if m["reasons"] else ""}</span></div>',
                    unsafe_allow_html=True,
                )

        if plan["avoid_buying"]:
            ui.section_label("Already well stocked — avoid rebuying")
            st.markdown(
                '<div class="wl-card">' + " · ".join(plan["avoid_buying"]) + "</div>",
                unsafe_allow_html=True,
            )

    with right:
        ui.section_label("Expiry health")
        charts.urgency_donut(esum, key="dash_donut")
        ui.section_label("Recent activity")
        if activity:
            rows = "".join(
                f"<tr><td>{r['event_date']}</td><td>{r['item_name']}</td>"
                f"<td>{r['quantity']} {r['unit']}</td>"
                f"<td>{ui.badge(r['event'].capitalize(), 'ok' if r['event']=='consumed' else 'high')}</td></tr>"
                for r in activity[:8]
            )
            st.markdown(
                f'<div class="wl-card"><table class="wl-table">'
                f"<tr><th>Date</th><th>Item</th><th>Qty</th><th>Event</th></tr>{rows}</table></div>",
                unsafe_allow_html=True,
            )
        else:
            ui.note("No consumption or waste events recorded yet. Mark items as used in My Pantry to build your history.", "info")

        ui.section_label("Waste risk (estimate)")
        level_color = {"high": "#B3261E", "medium": "#D35400", "low": "#1B7A43"}[risk["level"]]
        st.markdown(ui.progress_bar(min(risk["score"] * 10, 100), level_color), unsafe_allow_html=True)
        st.caption(f"Risk level: **{risk['level']}** — {risk['basis']}")
