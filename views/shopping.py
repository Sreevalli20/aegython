"""Shopping List — list management, restock suggestions, duplicate guard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import ui
from src import shopping_engine, validators
from src.shopping_engine import ShoppingError


def render(db_path=None) -> None:
    ui.page_header(
        "Shopping List",
        "Smart restocking: we compare against your pantry so you don't buy duplicates.",
    )

    items = shopping_engine.list_items(include_purchased=True, db_path=db_path)
    pending = [i for i in items if not i["purchased"]]
    est = shopping_engine.estimate_total(db_path=db_path)

    ui.metric_cards([
        {"value": len(pending), "label": "Items to buy"},
        {"value": len([i for i in items if i["purchased"]]), "label": "Purchased"},
        {"value": ui.fmt_money(est), "label": "Est. total cost (with prices)"},
        {"value": len(shopping_engine.restock_suggestions(db_path=db_path)),
         "label": "Auto restock suggestions"},
    ])

    # --- Add item with live pantry check ---
    ui.section_label("Add item")
    name_in = st.text_input("Ingredient", key="shop_name", placeholder="e.g. Olive Oil")
    match = None
    if name_in.strip():
        match = shopping_engine.pantry_match(name_in, db_path=db_path)
        if match:
            ui.note(
                f"Pantry check: you already have **{', '.join(match['names'])}** "
                f"(~{match['total_quantity']} {match['units'][0] if match['units'] else ''} in stock). "
                "Add anyway only if you need more.",
                "warn",
            )
    with st.form("shop_add_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        qty = c1.number_input("Quantity", min_value=0.001, value=1.0, key="shop_qty")
        unit = c2.selectbox("Unit", validators.VALID_UNITS, key="shop_unit")
        price = c3.number_input("Est. price ($)", min_value=0.0, value=0.0, step=0.5, key="shop_price")
        source = c4.selectbox("Source", ["manual", "restock", "recipe_gap"], key="shop_source")
        submitted = st.form_submit_button("Add to list", type="primary", width="stretch")
    if submitted:
        if not name_in.strip():
            st.error("Please enter an ingredient name.")
        else:
            try:
                shopping_engine.add_item(
                    name_in, quantity=qty, unit=unit,
                    price_estimate=price if price > 0 else None,
                    source=source, db_path=db_path)
                st.success(f"Added '{name_in.strip()}' to your shopping list.")
                st.rerun()
            except ShoppingError as exc:
                st.error(str(exc))
            except ValueError as exc:
                st.error(str(exc))

    # --- Restock suggestions ---
    restock = shopping_engine.restock_suggestions(db_path=db_path)
    restock_pending = [r for r in restock if not r["already_listed"]]
    if restock_pending:
        ui.section_label("Suggested restocks (below your thresholds)")
        for r in restock_pending[:8]:
            it = r["item"]
            cc1, cc2 = st.columns([4, 1])
            with cc1:
                ui.raw_html(
                    f'<div class="wl-card" style="padding:10px 16px;margin-bottom:6px">'
                    f'<b>{ui.esc(it["name"])}</b> — {it["quantity"]} {it["unit"]} left, '
                    f'threshold {it["min_threshold"]} {it["unit"]}</div>'
                )
            if cc2.button("Add", key=f"rs_add_{it['id']}", width="stretch"):
                try:
                    shopping_engine.add_item(it["name"], quantity=r["suggested_qty"],
                                              unit=it["unit"], source="restock", db_path=db_path)
                    st.success("Added.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    # --- List table ---
    ui.section_label("Shopping list")
    if not items:
        ui.empty_state("🛒", "Your shopping list is empty",
                       "Add items above — or cook a suggested meal and add its missing ingredients.")
        return

    rows = [{
        "ID": i["id"], "Item": i["name"],
        "Qty": f"{i['quantity']} {i['unit']}",
        "Est. price": ui.fmt_money(i.get("price_estimate")),
        "Status": "Purchased" if i["purchased"] else "To buy",
        "Added": i["added_date"], "Source": i["source"],
    } for i in items]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # --- Row actions ---
    pending_items = [i for i in items if not i["purchased"]]
    purchased_items = [i for i in items if i["purchased"]]

    if pending_items:
        ui.section_label("Actions on pending items")
        sel = st.selectbox(
            "Select item", options=[i["id"] for i in pending_items],
            format_func=lambda i: next(x["name"] for x in pending_items if x["id"] == i),
            key="shop_sel")
        c1, c2 = st.columns(2)
        if c1.button("Mark as purchased", key="shop_buy", width="stretch"):
            shopping_engine.mark_purchased(sel, db_path=db_path)
            st.success("Marked as purchased.")
            st.rerun()
        if c2.button("Remove from list", key="shop_remove", width="stretch"):
            shopping_engine.remove_item(sel, db_path=db_path)
            st.success("Removed.")
            st.rerun()

    if purchased_items:
        ui.section_label("Clear purchased")
        st.caption("Remove all purchased items from the list.")
        if st.button("Clear purchased items", key="shop_clear", width="stretch"):
            n = shopping_engine.clear_purchased(db_path=db_path)
            st.success(f"Cleared {n} purchased item(s).")
            st.rerun()
