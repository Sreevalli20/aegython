"""Expiry Intelligence — explainable urgency classification for every item."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from src import expiry_engine, inventory

FILTERS = {
    "all": "All items",
    "attention": "Needs attention (expired/critical/high)",
    "expired": "Expired",
    "critical": "Use today",
    "high": "Expiring soon (≤3 days)",
    "medium": "Plan to use (≤7 days)",
    "ok": "Fresh",
    "none": "No date",
}


def render(db_path=None) -> None:
    ui.page_header(
        "Expiry Intelligence",
        "Every item is classified with written reasoning. Dates come from package labels "
        "or your entries — this engine surfaces them, it does not judge food safety.",
    )

    items = inventory.list_items(db_path=db_path, status="active")
    assessed = expiry_engine.assess_inventory(items=items)
    esum = expiry_engine.summary(assessed)

    if not assessed:
        ui.empty_state("📅", "Nothing to assess",
                       "Add ingredients with expiry dates in My Pantry.")
        return

    ui.metric_cards([
        {"value": esum["needs_attention"], "label": "Need attention",
         "delta_kind": "bad" if esum["needs_attention"] else "good"},
        {"value": esum["expired"], "label": "Past date"},
        {"value": esum["critical"], "label": "Use today / tomorrow"},
        {"value": esum["ok"] + esum["none"], "label": "Fresh or undated"},
    ])

    left, right = st.columns([1, 2])
    with left:
        charts.urgency_donut(esum, key="expiry_donut")

    with right:
        st.caption(
            "**How urgency is computed:** days remaining = expiry date − today. "
            "Expired <0d · Use today ≤1d · Expiring soon ≤3d · Plan to use ≤7d · Fresh >7d. "
            "A **use-by** date is safety-critical: always follow the package label. "
            "A **best-before** date concerns quality. The engine never declares food safe "
            "or unsafe — it tells you what the label says and suggests a sensible action."
        )

    choice = st.radio("Filter", list(FILTERS.keys()),
                      format_func=lambda k: FILTERS[k], horizontal=True,
                      label_visibility="collapsed")

    if choice == "attention":
        shown = [a for a in assessed if a["urgency"] in ("expired", "critical", "high")]
    elif choice == "all":
        shown = assessed
    else:
        shown = [a for a in assessed if a["urgency"] == choice]

    if not shown:
        ui.note("No items in this category — nice and calm.", "info")
        return

    rows = [{
        "Ingredient": a["name"], "Qty": f"{a['quantity']} {a['unit']}",
        "Location": a["location"],
        "Expiry": a["expiry_date"] or "No date",
        "Days left": pd.NA if a["days_remaining"] is None else int(a["days_remaining"]),
        "Date type": a["date_label"], "Urgency": a["urgency"],
    } for a in shown]
    df = pd.DataFrame(rows).astype({"Days left": "Int64"})
    st.dataframe(
        df, width="stretch", hide_index=True,
        column_config={"Days left": st.column_config.NumberColumn(format="%d", width="small")},
    )

    ui.section_label("Item-by-item reasoning")
    for a in shown:
        color = {"expired": "#B3261E", "critical": "#C0392B", "high": "#D35400",
                 "medium": "#B8860B", "ok": "#1B7A43", "none": "#6B7280"}[a["urgency"]]
        days = a["days_remaining"]
        days_txt = "no date" if days is None else (f"{days}d ago" if days < 0 else f"in {days}d")
        reasons = " ".join(a["reasons"])
        st.markdown(
            f'<div class="wl-card" style="border-left:4px solid {color}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<b>{a["name"]}</b> {ui.urgency_badge(a["urgency"])}'
            f'<span style="color:#6B7280;font-size:.82rem">{days_txt} · '
            f'{a["quantity"]} {a["unit"]} · {a["location"]}</span></div>'
            f'<div style="font-size:.85rem;color:#33413a;margin-top:6px">{reasons}</div>'
            f'<div style="font-size:.85rem;margin-top:4px"><b>Suggested action:</b> {a["action"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # quick actions for problem items
        if a["item_id"] and a["urgency"] in ("expired", "critical", "high"):
            c1, c2 = st.columns(2)
            if c1.button(f"Mark {a['name']} as used", key=f"exp_use_{a['item_id']}", width="stretch"):
                inventory.mark_event(a["item_id"], "consumed", "Used after expiry alert",
                                     db_path=db_path)
                st.success("Marked as consumed.")
                st.rerun()
            if c2.button(f"Log {a['name']} as wasted", key=f"exp_waste_{a['item_id']}", width="stretch"):
                inventory.mark_event(a["item_id"], "wasted", "Expired before use",
                                     db_path=db_path)
                st.success("Waste event logged for analytics.")
                st.rerun()
