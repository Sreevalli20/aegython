"""Home Dashboard — inventory summary, expiry alerts, plan, activity."""

from __future__ import annotations

import streamlit as st

from components import charts, imagery, ui
from src import analytics_engine, expiry_engine, inventory, shopping_engine, waste_engine


def _shopping_rec_card(r: dict, db_path) -> None:
    it = r["item"]
    photo = imagery.ingredient_photo(it["name"])
    thumb = ""
    if photo:
        thumb = (
            f'<div style="width:44px;height:44px;border-radius:11px;overflow:hidden;'
            f'flex-shrink:0;background:linear-gradient(135deg,#1E5B3A,#3E7C59)">'
            f'<img src="{ui.esc(photo)}" style="width:100%;height:100%;'
            f'object-fit:cover" onerror="this.remove()"/></div>'
        )
    ui.raw_html(
        '<div class="wl-card wl-action-row" style="padding:10px 16px;margin-bottom:8px">'
        f'{thumb}<span class="wl-action-text">'
        f'<b>{ui.esc(it["name"])}</b> — {it["quantity"]} {it["unit"]} left '
        f'(low-stock alert at {it["min_threshold"]})</span></div>'
    )
    if not r["already_listed"]:
        if st.button(f"Add {it['name']} to shopping list",
                     key=f"dash_restock_{it['id']}", width="content"):
            try:
                shopping_engine.add_item(
                    it["name"], quantity=max(r["suggested_qty"], it["min_threshold"]),
                    unit=it["unit"], source="restock", db_path=db_path)
                st.success(f"Added '{it['name']}' to your shopping list.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _meal_card(m: dict, idx: int) -> None:
    exp_chip = ""
    if m["expiring_ingredients"]:
        names = ", ".join(ui.esc(n) for n in m["expiring_ingredients"][:3])
        exp_chip = ui.badge(f"⏳ Uses expiring: {names}", "high")
    meta = " · ".join(x for x in [
        m.get("cuisine"), m.get("meal_type"),
        f"~{m['prep_time_min']} min" if m.get("prep_time_min") else "",
        f"{m['servings']} servings" if m.get("servings") else "",
    ] if x)
    reason = ui.esc(m["reasons"][0]) if m.get("reasons") else ""
    match_color = ("#1E5B3A" if m["match_pct"] >= 70
                   else "#D35400" if m["match_pct"] >= 40 else "#6B7280")
    body = (
        f'<div style="margin-top:8px">{exp_chip}</div>' if exp_chip else ""
    ) + (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-top:8px">'
        f'<span style="font-size:.8rem;color:#71806F">{ui.esc(meta)}</span>'
        f'<span style="font-family:Fraunces,Georgia,serif;font-size:1.25rem;'
        f'font-weight:700;color:{match_color}">{m["match_pct"]:.0f}%</span></div>'
        f'<div style="font-size:.82rem;color:#71806F;margin-top:4px">{reason}</div>'
    )
    extra = (
        f'<div style="text-align:right">'
        f'<div style="font-family:Fraunces,Georgia,serif;font-size:1.3rem;'
        f'font-weight:700;color:{match_color}">{m["match_pct"]:.0f}%</div>'
        f'<div style="font-size:.7rem;color:#71806F">pantry match</div></div>'
    )
    ui.raw_html(imagery.recipe_card(m, idx, extra_html=extra, body_html=body))


def render(db_path=None) -> None:
    items = inventory.list_items(db_path=db_path, status="active")
    assessed = expiry_engine.assess_inventory(items=items)
    esum = expiry_engine.summary(assessed)
    plan = waste_engine.build_daily_plan(db_path=db_path, assessed=assessed)
    risk = waste_engine.waste_risk_score(assessed, db_path=db_path)
    activity = inventory.recent_activity(limit=8, db_path=db_path)
    summary = analytics_engine.consumption_summary(db_path=db_path)
    restock = shopping_engine.restock_suggestions(db_path=db_path)

    ui.page_header(
        "Good morning — here's your kitchen at a glance",
        "Know what you have. Know what to use. Waste less.",
    )

    if not items:
        ui.empty_state(
            "🥬", "Your pantry is empty",
            "Add ingredients manually or load the sample household data to explore WasteLess AI.",
            "Load sample data", "load_sample",
        )
        if st.session_state.get("pending_action") == "load_sample":
            n = inventory.add_sample_data(db_path=db_path)
            st.session_state.pop("pending_action", None)
            st.success(f"Loaded {n} sample items.")
            st.rerun()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add your first item", width="stretch"):
                ui.navigate("pantry")
                st.rerun()
        return

    # --- Metric cards -------------------------------------------------------
    ui.metric_cards([
        {"value": esum["total"], "label": "Items in inventory", "icon": "🥫",
         "delta": f"{esum['needs_attention']} need attention",
         "delta_kind": "bad" if esum["needs_attention"] else "good"},
        {"value": esum["expired"] + esum["critical"], "label": "Expired / use today",
         "icon": "⏰",
         "delta_kind": "bad" if (esum["expired"] + esum["critical"]) else "good"},
        {"value": esum["high"] + esum["medium"], "label": "Expiring this week",
         "icon": "📅"},
        {"value": ui.fmt_money(analytics_engine.inventory_value(db_path=db_path)),
         "label": "Est. inventory value", "icon": "💰"},
        {"value": ui.fmt_money(summary["wasted_value"]),
         "label": "Est. value wasted (recorded)", "icon": "♻️",
         "delta": f"{summary['wasted_events']} waste events",
         "delta_kind": "bad" if summary["wasted_value"] else "good"},
    ])

    left, right = st.columns([3, 2])

    with left:
        ui.section_label("Today's food-saving plan")
        if plan["actions"]:
            for a in plan["actions"][:6]:
                color = {"high": "#B3261E", "medium": "#D35400", "low": "#1E5B3A"}[a["priority"]]
                icon = {"expiry": "⚠️", "meal": "🍽️", "restock": "🛒"}.get(a["type"], "•")
                ui.raw_html(ui.action_row(icon, ui.esc(a["text"]), color))
        else:
            ui.note("Nothing needs urgent attention — your inventory is in great shape. 🎉", "info")

        if plan["top_meals"]:
            ui.section_label("What to cook tonight")
            for i, m in enumerate(plan["top_meals"][:3], 1):
                _meal_card(m, i)

        if plan["avoid_buying"]:
            ui.section_label("Already well stocked — skip these")
            chips = "".join(ui.chip(p) for p in plan["avoid_buying"])
            ui.raw_html(f'<div class="wl-card" style="padding:14px 18px">{chips}</div>')

    with right:
        ui.section_label("Expiry health")
        charts.urgency_donut(esum, key="dash_donut")

        ui.section_label("Waste risk")
        level_color = {"high": "#B3261E", "medium": "#D35400", "low": "#1E5B3A"}[risk["level"]]
        ui.raw_html(ui.progress_bar(min(risk["score"] * 10, 100), level_color))
        st.caption(f"Current level: **{risk['level']}** — based on how many items are expired or expiring soon.")

    # --- Bottom row: shopping recs / inventory mix / activity ----------------
    b1, b2, b3 = st.columns([1.1, 1, 1.2])

    with b1:
        ui.section_label("Shopping recommendations")
        pending_restock = [r for r in restock if not r["already_listed"]]
        if pending_restock:
            for r in pending_restock[:4]:
                _shopping_rec_card(r, db_path)
            st.caption("Items at or below the low-stock alerts you set.")
        else:
            ui.note("No restock needs right now — your stock levels look healthy. ✅", "info")
        st.caption("Review everything in **Shopping List**.")

    with b2:
        ui.section_label("Inventory by category")
        charts.category_inventory_chart(items, key="dash_cat_inv")

    with b3:
        ui.section_label("Recent activity")
        if activity:
            rows = "".join(
                f"<tr><td>{ui.esc(r['event_date'])}</td><td>{ui.esc(r['item_name'])}</td>"
                f"<td>{ui.esc(r['quantity'])} {ui.esc(r['unit'])}</td>"
                f"<td>{ui.badge(r['event'].capitalize(), 'ok' if r['event']=='consumed' else 'high')}</td></tr>"
                for r in activity[:8]
            )
            ui.raw_html(
                f'<div class="wl-card"><table class="wl-table">'
                f"<tr><th>Date</th><th>Item</th><th>Qty</th><th>Event</th></tr>{rows}</table></div>"
            )
        else:
            ui.note("No activity yet — mark items as used in **My Pantry** to build your history.", "info")
