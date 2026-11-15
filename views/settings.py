"""Settings & About — data management, privacy, attribution."""

from __future__ import annotations

import streamlit as st

from components import ui
from src import database, inventory


def render(db_path=None) -> None:
    ui.page_header("Settings", "Your data, your privacy, and about the app.")

    ui.section_label("Your data")
    ui.raw_html(
        '<div class="wl-card"><b>Private by design.</b> WasteLess AI keeps your '
        'pantry, shopping list and activity history safely stored — no accounts '
        'needed, and your food data is never sent to external services.<br/><br/>'
        '<b>Good to know:</b> on Streamlit Cloud, stored data can reset if the '
        'app is redeployed, unless a persistent storage volume is configured.<br/><br/>'
        '<b>Demo tip:</b> use "Load sample household data" below to explore the '
        'app with realistic data in seconds.</div>'
    )

    c1, c2 = st.columns(2)
    if c1.button("Load sample household data", width="stretch"):
        n = inventory.add_sample_data(db_path=db_path)
        st.success(f"Loaded {n} sample items.")
        st.rerun()

    if "confirm_clear" not in st.session_state:
        st.session_state["confirm_clear"] = False
    if c2.button("Clear ALL local data", type="secondary", width="stretch"):
        st.session_state["confirm_clear"] = True
    if st.session_state["confirm_clear"]:
        ui.note("This will permanently delete your pantry, shopping list and all "
                "activity history. This cannot be undone.", "danger")
        d1, d2 = st.columns(2)
        if d1.button("Yes — delete everything", type="primary", width="stretch"):
            database.clear_all_data(db_path=db_path)
            st.session_state["confirm_clear"] = False
            st.success("All data cleared.")
            st.rerun()
        if d2.button("Cancel", width="stretch"):
            st.session_state["confirm_clear"] = False
            st.rerun()

    ui.section_label("About WasteLess AI")
    ui.raw_html(
        '<div class="wl-card"><b>WasteLess AI</b> helps households waste less '
        "food by tracking what's in the kitchen, flagging what expires soon, "
        "suggesting meals from what you already have, and watching for "
        "duplicate purchases.<br/><br/>"
        "<b>Smart features:</b> expiry alerts with plain-language guidance, "
        "recipe recommendations matched to your pantry, low-stock reminders, "
        "shopping-list duplicate checks, waste analytics and what-if "
        "simulations.<br/><br/>"
        "<b>Safety first:</b> expiry dates are labels, not safety verdicts. For "
        "use-by dates, always follow the package instructions and your local "
        "food-safety guidance.</div>"
    )
