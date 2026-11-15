"""Waste Prevention — daily actionable plan and duplicate-purchase guard."""

from __future__ import annotations

import streamlit as st

from components import imagery, ui
from src import expiry_engine, inventory, shopping_engine, waste_engine


def render(db_path=None) -> None:
    ui.page_header(
        "Waste Prevention",
        "Your daily plan to use food before it expires — built only from your real pantry.",
    )

    assessed = expiry_engine.assess_inventory(db_path=db_path)
    plan = waste_engine.build_daily_plan(db_path=db_path, assessed=assessed)
    risk = waste_engine.waste_risk_score(assessed, db_path=db_path)

    if not assessed:
        ui.empty_state("🛡️", "No inventory to protect",
                       "Add ingredients first — your plan is generated from live pantry data.")
        return

    ui.metric_cards([
        {"value": plan["stats"]["expiring_count"], "label": "Items expiring soon", "icon": "⏰",
         "delta_kind": "bad" if plan["stats"]["expiring_count"] else "good"},
        {"value": plan["stats"]["meal_options"], "label": "Meal options today", "icon": "🍽️"},
        {"value": risk["level"].title(), "label": "Waste risk (estimate)", "icon": "📈",
         "delta": f"{risk['expired_items_logged']} waste events logged",
         "delta_kind": "bad" if risk["expired_items_logged"] else "good"},
    ])

    left, right = st.columns([3, 2])
    with left:
        ui.section_label("Priority actions")
        if plan["actions"]:
            for a in plan["actions"]:
                color = {"high": "#B3261E", "medium": "#D35400", "low": "#1E5B3A"}[a["priority"]]
                icon = {"expiry": "⚠️", "meal": "🍽️", "restock": "🛒"}[a["type"]]
                ui.raw_html(ui.action_row(icon, ui.esc(a["text"]), color))
        else:
            ui.note("No urgent actions — everything is fresh and well stocked. ✨", "info")

        ui.section_label("Cook down expiring stock")
        for m in plan["top_meals"]:
            exp_badge = ('<span class="wl-badge high" style="margin-left:6px">uses expiring items</span>'
                         if m["expiring_ingredients"] else "")
            reasons = " ".join(m["reasons"][:2])
            photo = imagery.recipe_photo(m)
            ui.raw_html(
                f'<div class="wl-card" style="padding:10px 16px;margin-bottom:8px;'
                f'display:flex;gap:14px;align-items:center">'
                f'<div style="width:56px;height:56px;border-radius:12px;overflow:hidden;'
                f'flex-shrink:0;background:linear-gradient(135deg,#1E5B3A,#3E7C59)">'
                f'<img src="{ui.esc(photo)}" style="width:100%;height:100%;object-fit:cover" '
                f'onerror="this.remove()"/></div>'
                f'<div><b>{ui.esc(m["recipe"])}</b> — {m["match_pct"]}% pantry match{exp_badge}<br/>'
                f'<span style="font-size:.83rem;color:#71806F">{ui.esc(reasons)}</span></div></div>'
            )

    with right:
        ui.section_label("Don't buy again")
        if plan["avoid_buying"]:
            chips = "".join(ui.chip(p, "gold") for p in plan["avoid_buying"])
            ui.raw_html(f'<div class="wl-card" style="padding:14px 18px">{chips}</div>')
        else:
            ui.note("No surplus stock detected right now.", "info")

        ui.section_label("Duplicate-purchase check")
        st.caption("About to buy something? Check your pantry first.")
        name = st.text_input("Ingredient to check", key="dup_check",
                             placeholder="e.g. Milk, Chicken Breast, Eggs")
        if name.strip():
            match = shopping_engine.pantry_match(name, db_path=db_path)
            if match:
                ui.note(
                    f"**Already in your pantry:** {', '.join(match['names'])} — "
                    f"about {match['total_quantity']} {match['units'][0] if match['units'] else 'units'} in stock. "
                    "Buying more may create duplicates.",
                    "warn",
                )
            else:
                ui.note("Not found in your pantry — safe to consider buying. ✅", "info")
