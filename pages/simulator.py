"""What-if Simulator — hypothetical scenarios on real inventory."""

from __future__ import annotations

import streamlit as st

from components import ui
from src import inventory, simulator

if "sim_purchases" not in st.session_state:
    st.session_state["sim_purchases"] = []


def render(db_path=None) -> None:
    ui.page_header(
        "What-if Simulator",
        "Model hypothetical changes against your real inventory. All outputs are "
        "estimates — directional insight, not predictions.",
    )

    items = inventory.list_items(db_path=db_path, status="active")
    if not items:
        ui.empty_state("🧪", "Nothing to simulate",
                       "Add ingredients to your pantry first.")
        return

    ui.note(
        "Adjust the scenario below, then run the simulation. "
        "The engine re-computes expiry exposure, meal options and estimated waste "
        "using your actual inventory plus hypothetical additions.",
        "info",
    )

    # --- Scenario builder: hypothetical purchases ---
    ui.section_label("Hypothetical purchases (added for simulation only)")
    with st.form("sim_add_purchase", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        pname = c1.text_input("Item name")
        pqty = c2.number_input("Qty", min_value=0.1, value=1.0)
        punit = c3.selectbox("Unit", ["pcs", "g", "kg", "ml", "l", "can", "pack"])
        pshelf = c4.number_input("Shelf life (days)", min_value=1, max_value=365, value=7)
        pprice = st.number_input("Est. price ($)", min_value=0.0, value=0.0, step=0.5)
        if st.form_submit_button("Add to scenario"):
            if pname.strip():
                st.session_state["sim_purchases"].append({
                    "name": pname.strip(), "quantity": pqty, "unit": punit,
                    "shelf_days": pshelf, "price": pprice or None,
                })
                st.rerun()

    if st.session_state["sim_purchases"]:
        for idx, p in enumerate(st.session_state["sim_purchases"]):
            st.markdown(
                f'<span class="wl-badge info" style="margin:2px">'
                f'{p["name"]} · {p["quantity"]} {p["unit"]} · {p["shelf_days"]}d shelf'
                f'</span>', unsafe_allow_html=True)
        if st.button("Clear scenario purchases", width="stretch"):
            st.session_state["sim_purchases"] = []
            st.rerun()

    # --- Behavioral assumptions ---
    ui.section_label("Behavioral assumptions")
    c1, c2, c3 = st.columns(3)
    daily_consumption = c1.slider(
        "Extra daily consumption", 0.0, 1.0, 0.0, 0.05,
        help="Fraction of total inventory assumed eaten per day (0–100%).",
        key="sim_consumption")
    waste_rate = c2.slider(
        "Waste rate for expiring items", 0.0, 1.0, 0.2, 0.05,
        help="Fraction of at-risk expiring quantity assumed wasted.",
        key="sim_waste")
    run = c3.button("Run simulation", type="primary", width="stretch")

    if run or st.session_state.get("sim_ran"):
        st.session_state["sim_ran"] = True
        result = simulator.simulate(
            db_path=db_path,
            extra_purchases=st.session_state["sim_purchases"],
            daily_extra_consumption=daily_consumption,
            waste_rate_today=waste_rate,
        )

        ui.section_label("Baseline vs scenario")
        b, s, d = result["baseline"], result["scenario"], result["delta"]
        cols = st.columns(3)
        for col, label, base_v, scen_v in [
            (cols[0], "Active items", b["active_items"], s["active_items"]),
            (cols[1], "Items needing attention", b["needs_attention"], s["needs_attention"]),
            (cols[2], "Expired items", b["expired"], s["expired"]),
        ]:
            delta = scen_v - base_v
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "•"
            col.metric(label, f"{base_v} → {scen_v}",
                       delta=f"{arrow} {abs(delta)} vs baseline")

        m1, m2, m3 = st.columns(3)
        m1.metric("Meal options in scenario", s["meal_options"])
        m2.metric("Est. daily utilization", f"{s['estimated_daily_utilization_pct']}%")
        m3.metric("Est. value at risk", ui.fmt_money(s["estimated_waste_value_at_risk"]))

        if s["meal_options"] > b.get("meal_options", 0) or d["items_change"] > 0:
            ui.note(
                "The simulation suggests your scenario could change meal options and "
                "expiry exposure. Review the numbers above — they are estimates only.",
                "info",
            )

        ui.note(result["disclaimer"], "warn")
