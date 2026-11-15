"""My Pantry — full CRUD inventory management."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import ui
from src import expiry_engine, inventory, shopping_engine, validators
from src.inventory import InventoryError

CATEGORIES = validators.VALID_CATEGORIES
LOCATIONS = validators.VALID_LOCATIONS
UNITS = validators.VALID_UNITS
DATE_TYPES = validators.VALID_DATE_TYPES


def _flash_result(msg: str, ok: bool = True) -> None:
    (st.success if ok else st.error)(msg)


def _add_form(db_path) -> None:
    ui.section_label("Add ingredient")
    with st.form("add_item_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Ingredient name *", placeholder="e.g. Chicken Breast")
        category = c2.selectbox("Category", CATEGORIES)
        location = c3.selectbox("Storage location", LOCATIONS)
        c4, c5, c6 = st.columns(3)
        quantity = c4.number_input("Quantity", min_value=0.001, step=1.0, value=1.0)
        unit = c5.selectbox("Unit", UNITS)
        price = c6.number_input("Est. price ($)", min_value=0.0, step=0.5, value=0.0)
        c7, c8, c9 = st.columns(3)
        purchase = c7.date_input("Purchase date", value=None)
        expiry = c8.date_input("Expiry / best-before date", value=None)
        date_type = c9.selectbox("Date type", DATE_TYPES,
                                 format_func=lambda d: validators.DATE_TYPE_LABELS[d])
        threshold = st.number_input("Low-stock alert threshold (0 = off)",
                                    min_value=0.0, step=1.0, value=0.0)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Add to pantry", type="primary",
                                          use_container_width=True)
    if submitted:
        try:
            iid = inventory.add_item({
                "name": name, "category": category, "location": location,
                "quantity": quantity, "unit": unit,
                "price": price if price > 0 else None,
                "purchase_date": purchase.isoformat() if purchase else None,
                "expiry_date": expiry.isoformat() if expiry else None,
                "date_type": date_type,
                "min_threshold": threshold, "notes": notes,
            }, db_path=db_path)
            st.success(f"Added '{name}' to your pantry.")
            st.rerun()
        except (InventoryError, ValueError) as exc:
            st.error(str(exc))


def _edit_form(selected: dict, db_path) -> None:
    ui.section_label(f"Edit: {selected['name']} (#{selected['id']})")
    with st.form(f"edit_item_{selected['id']}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Ingredient name", value=selected["name"])
        category = c2.selectbox("Category", CATEGORIES, index=CATEGORIES.index(selected["category"]) if selected["category"] in CATEGORIES else len(CATEGORIES)-1)
        location = c3.selectbox("Location", LOCATIONS, index=LOCATIONS.index(selected["location"]) if selected["location"] in LOCATIONS else 0)
        c4, c5, c6 = st.columns(3)
        quantity = c4.number_input("Quantity", min_value=0.001, step=1.0, value=float(selected["quantity"]))
        unit = c5.selectbox("Unit", UNITS, index=UNITS.index(selected["unit"]) if selected["unit"] in UNITS else 0)
        price = c6.number_input("Est. price ($)", min_value=0.0, step=0.5,
                                value=float(selected["price"] or 0))
        c7, c8, c9 = st.columns(3)
        def _pdate(s):
            from datetime import date
            try:
                return date.fromisoformat(s)
            except Exception:
                return None
        purchase = c7.date_input("Purchase date", value=_pdate(selected["purchase_date"]))
        expiry = c8.date_input("Expiry date", value=_pdate(selected["expiry_date"]))
        date_type = c9.selectbox("Date type", DATE_TYPES,
                                 index=DATE_TYPES.index(selected["date_type"]) if selected["date_type"] in DATE_TYPES else 2,
                                 format_func=lambda d: validators.DATE_TYPE_LABELS[d])
        threshold = st.number_input("Low-stock threshold", min_value=0.0, step=1.0,
                                    value=float(selected["min_threshold"] or 0))
        notes = st.text_input("Notes", value=selected.get("notes", ""))
        submitted = st.form_submit_button("Save changes", type="primary",
                                          use_container_width=True)
    if submitted:
        try:
            inventory.update_item(selected["id"], {
                "name": name, "category": category, "location": location,
                "quantity": quantity, "unit": unit,
                "price": price if price > 0 else None,
                "purchase_date": purchase.isoformat(),
                "expiry_date": expiry.isoformat() if expiry else None,
                "date_type": date_type, "min_threshold": threshold, "notes": notes,
            }, db_path=db_path)
            st.success("Item updated.")
            st.rerun()
        except (InventoryError, ValueError) as exc:
            st.error(str(exc))


def render(db_path=None) -> None:
    ui.page_header("My Pantry", "Add, edit and track every ingredient in your kitchen.")

    items = inventory.list_items(db_path=db_path, status="active")
    assessed = {a["item_id"]: a for a in expiry_engine.assess_inventory(items=items)}
    restock = shopping_engine.restock_suggestions(db_path=db_path)

    low_stock = [r for r in restock]
    expiring = [i for i in items if (assessed.get(i["id"]) or {}).get("urgency") in ("expired", "critical", "high")]

    ui.metric_cards([
        {"value": len(items), "label": "Active items"},
        {"value": len(expiring), "label": "Expiring soon",
         "delta_kind": "bad" if expiring else "good"},
        {"value": len(low_stock), "label": "Below restock threshold"},
        {"value": len(inventory.recent_activity(limit=100, db_path=db_path)),
         "label": "Logged events (all time)"},
    ])

    if not items:
        ui.empty_state("📦", "No ingredients yet",
                       "Add your first item below, or load the sample dataset.",
                       "Load sample data", "pantry_load_sample")
        if st.session_state.get("pending_action") == "pantry_load_sample":
            n = inventory.add_sample_data(db_path=db_path)
            st.session_state.pop("pending_action", None)
            st.success(f"Loaded {n} sample items.")
            st.rerun()

    tab_list, tab_add = st.tabs(["Inventory", "➕ Add item"])

    with tab_add:
        _add_form(db_path)

    with tab_list:
        # --- Filters ---
        f1, f2, f3, f4 = st.columns(4)
        search = f1.text_input("Search", placeholder="e.g. chicken", key="pantry_search")
        category = f2.selectbox("Category", ["All"] + CATEGORIES, key="pantry_cat")
        location = f3.selectbox("Location", ["All"] + LOCATIONS, key="pantry_loc")
        sort = f4.selectbox("Sort by", ["expiry", "name", "added", "price", "quantity"],
                            format_func=lambda s: {"expiry": "Expiry date", "name": "Name",
                                                   "added": "Recently added", "price": "Price",
                                                   "quantity": "Quantity"}[s], key="pantry_sort")

        filtered = inventory.list_items(db_path=db_path, status="active",
                                        category=category, location=location,
                                        search=search, sort=sort)

        if not filtered:
            ui.empty_state("🔍", "No items match your filters",
                           "Try clearing the search or filters.")
        else:
            rows = []
            for it in filtered:
                a = assessed.get(it["id"], {})
                rows.append({
                    "ID": it["id"], "Ingredient": it["name"],
                    "Category": it["category"], "Qty": f"{it['quantity']} {it['unit']}",
                    "Location": it["location"],
                    "Expiry": it["expiry_date"] or "—",
                    "Days left": str(a.get("days_remaining")) if a.get("days_remaining") is not None else "—",
                    "Urgency": a.get("urgency", "none"),
                    "Price": ui.fmt_money(it.get("price")),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"ID": st.column_config.NumberColumn(width="small")})

        # --- Row actions ---
        ui.section_label("Item actions")
        active_items = inventory.list_items(db_path=db_path, status="active")
        if active_items:
            labels = {i["id"]: f"#{i['id']} — {i['name']} ({i['quantity']} {i['unit']})"
                      for i in active_items}
            sel_id = st.selectbox("Select an item", options=list(labels.keys()),
                                  format_func=lambda i: labels[i], key="pantry_sel")
            sel = inventory.get_item(sel_id, db_path=db_path)
            if sel:
                a = assessed.get(sel_id, {})
                st.markdown(
                    f'<div class="wl-card"><b>{sel["name"]}</b>'
                    f'<span style="float:right">{ui.urgency_badge(a.get("urgency","none"))}</span><br/>'
                    f'<span style="color:#6B7280;font-size:.85rem">'
                    f'{sel["quantity"]} {sel["unit"]} · {sel["location"]} · '
                    f'{sel["category"]} · expires {sel["expiry_date"] or "—"} '
                    f'({a.get("date_label","date")})</span><br/>'
                    f'<span style="font-size:.85rem">{a.get("action","")}</span></div>',
                    unsafe_allow_html=True,
                )
                c1, c2, c3, c4, c5 = st.columns(5)
                consume_qty = c1.number_input("Qty to consume", min_value=0.001,
                                              max_value=float(sel["quantity"]),
                                              value=min(1.0, float(sel["quantity"])),
                                              key=f"consume_qty_{sel_id}")
                if c1.button("Consume", key=f"consume_{sel_id}", use_container_width=True):
                    try:
                        res = inventory.consume_quantity(sel_id, consume_qty, db_path=db_path)
                        st.success(f"Consumed {res['quantity']} {res['unit']} of {res['item']}"
                                   + (f" (est. value {ui.fmt_money(res['est_value'])})" if res['est_value'] else ""))
                        st.rerun()
                    except (InventoryError, ValueError) as exc:
                        st.error(str(exc))
                if c2.button("Mark used", key=f"used_{sel_id}", use_container_width=True):
                    res = inventory.mark_event(sel_id, "consumed", "Used in cooking", db_path=db_path)
                    st.success(f"Marked {res['item']} as consumed.")
                    st.rerun()
                if c3.button("Mark wasted", key=f"waste_{sel_id}", use_container_width=True):
                    res = inventory.mark_event(sel_id, "wasted", "User reported waste", db_path=db_path)
                    st.success(f"Logged {res['item']} as wasted" +
                               (f" (est. {ui.fmt_money(res['est_value'])})" if res['est_value'] else "") + ".")
                    st.rerun()
                if c4.button("Delete", key=f"del_{sel_id}", use_container_width=True):
                    st.session_state[f"confirm_del_{sel_id}"] = True
                if c5.button("Edit", key=f"edit_{sel_id}", use_container_width=True):
                    st.session_state["edit_id"] = sel_id
                    st.rerun()

                if st.session_state.get(f"confirm_del_{sel_id}"):
                    ui.note(f"Delete '{sel['name']}' permanently? This cannot be undone.", "warn")
                    d1, d2 = st.columns(2)
                    if d1.button("Yes, delete", key=f"confirm_yes_{sel_id}", type="primary"):
                        inventory.delete_item(sel_id, db_path=db_path)
                        st.session_state.pop(f"confirm_del_{sel_id}", None)
                        st.success("Item deleted.")
                        st.rerun()
                    if d2.button("Cancel", key=f"confirm_no_{sel_id}"):
                        st.session_state.pop(f"confirm_del_{sel_id}", None)
                        st.rerun()

                if st.session_state.get("edit_id") == sel_id:
                    _edit_form(sel, db_path)

        # --- Restock suggestions ---
        if low_stock:
            ui.section_label("Restock suggestions (below threshold)")
            for r in low_stock[:6]:
                it = r["item"]
                already = " · already on shopping list" if r["already_listed"] else ""
                st.markdown(
                    f'<div class="wl-card" style="padding:10px 16px;margin-bottom:6px">'
                    f'<b>{it["name"]}</b> — {it["quantity"]} {it["unit"]} left '
                    f'(threshold {it["min_threshold"]}){already}</div>',
                    unsafe_allow_html=True,
                )
                if not r["already_listed"]:
                    if st.button(f"Add {it['name']} to shopping list",
                                 key=f"restock_{it['id']}"):
                        try:
                            shopping_engine.add_item(
                                it["name"], quantity=max(r["suggested_qty"], it["min_threshold"]),
                                unit=it["unit"], source="restock", db_path=db_path)
                            st.success("Added to shopping list.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
