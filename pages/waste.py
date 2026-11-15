"""Waste Prevention — daily actionable plan and duplicate-purchase guard."""

from __future__ import annotations

import streamlit as st

from components import ui
from src import expiry_engine, inventory, shopping_engine, waste_engine


def render(db_path=None) -> None:
    ui.page_header(
        "Waste Prevention",
        "A daily plan built only from your real inventory records and computed expiry assessments.",
    )

    assessed = expiry_engine.assess_inventory(db_path=db_path)
    plan = waste_engine.build_daily_plan(db_path=db_path, assessed=assessed)
    risk = waste_engine.waste_risk_score(assessed, db_path=db_path)

    if not assessed:
        ui.empty_state("🛡️", "No inventory to protect",
                       "Add ingredients first — the plan is generated from live data.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Items expiring soon", plan["stats"]["expiring_count"])
    col2.metric("Meal options today", plan["stats"]["meal_options"])
    col3.metric("Waste risk (est.)", risk["level"].title())

    st.markdown(f"**Risk basis:** {risk['basis']} · "
                f"Recorded waste events: {risk['expired_items_logged']} · "
                f"Est. wasted value: {ui.fmt_money(risk['estimated_waste_value'])}")

    left, right = st.columns([3, 2])
    with left:
        ui.section_label("Priority actions")
        if plan["actions"]:
            for a in plan["actions"]:
                color = {"high": "#B3261E", "medium": "#D35400", "low": "#1B7A43"}[a["priority"]]
                icon = {"expiry": "⚠️", "meal": "🍽️", "restock": "🛒"}[a["type"]]
                st.markdown(
                    f'<div class="wl-card" style="border-left:4px solid {color};padding:12px 16px;margin-bottom:8px">'
                    f'<span style="margin-right:8px">{icon}</span>{a["text"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            ui.note("No urgent actions — everything is fresh and well stocked.", "info")

        ui.section_label("How to cook down expiring stock")
        for m in plan["top_meals"]:
            st.markdown(
                f'<div class="wl-card" style="padding:10px 16px;margin-bottom:6px">'
                f'<b>{m["recipe"]}</b> — {m["match_pct"]}% pantry match'
                + (f' · <span class="wl-badge high">uses expiring items</span>'
                   if m["expiring_ingredients"] else "")
                + f'<br/><span style="font-size:.83rem;color:#33413a">{" ".join(m["reasons"][:2])}</span></div>',
                unsafe_allow_html=True,
            )

    with right:
        ui.section_label("Don't buy again")
        if plan["avoid_buying"]:
            for p in plan["avoid_buying"]:
                st.markdown(f'<div class="wl-card" style="padding:8px 14px;margin-bottom:6px">{p}</div>',
                            unsafe_allow_html=True)
        else:
            ui.note("No surplus stock detected.", "info")

        ui.section_label("Duplicate-purchase check")
        st.caption("Type an ingredient you are about to buy — we check your pantry first.")
        name = st.text_input("Ingredient to check", key="dup_check",
                             placeholder="e.g. Milk, Chicken Breast, Eggs")
        if name.strip():
            match = shopping_engine.pantry_match(name, db_path=db_path)
            if match:
                ui.note(
                    f"**You already have this:** {', '.join(match['names'])} — "
                    f"about {match['total_quantity']} {match['units'][0] if match['units'] else 'units'} in stock "
                    f"({', '.join(match['names'])}). Buying more may create duplicates.",
                    "warn",
                )
            else:
                ui.note("Not found in your pantry — safe to consider buying.", "info")
