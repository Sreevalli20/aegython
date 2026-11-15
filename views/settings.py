"""Settings & About — data management, privacy, attribution."""

from __future__ import annotations

import streamlit as st

from components import ui
from src import database, inventory


def render(db_path=None) -> None:
    ui.page_header("Settings", "Data, privacy and app information.")

    ui.section_label("Local data")
    ui.raw_html(
        '<div class="wl-card"><b>Local storage:</b> WasteLess AI keeps all data '
        'in a SQLite database on this machine — no accounts, no cloud sync, '
        'no external AI APIs.<br/><br/>'
        'On <b>Streamlit Cloud</b> the filesystem is temporary by default: data '
        'can reset when the app redeploys or the instance is replaced. Set the '
        '<code>WASTELESS_DB_PATH</code> environment variable to a mounted '
        'persistent volume for production use.<br/><br/>'
        '<b>What is stored:</b> pantry items, consumption/waste events and your '
        'shopping list — nothing else.<br/><br/>'
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
                "activity logs. This cannot be undone.", "danger")
        d1, d2 = st.columns(2)
        if d1.button("Yes — delete everything", type="primary", width="stretch"):
            database.clear_all_data(db_path=db_path)
            st.session_state["confirm_clear"] = False
            st.success("All local data cleared.")
            st.rerun()
        if d2.button("Cancel", width="stretch"):
            st.session_state["confirm_clear"] = False
            st.rerun()

    ui.section_label("About WasteLess AI")
    ui.raw_html(
        '<div class="wl-card"><b>WasteLess AI</b> — an offline-first household food '
        "waste prevention platform.<br/><br/>"
        "<b>Intelligence:</b> TF-IDF + cosine-similarity recipe matching, "
        "IDF-weighted ingredient coverage, expiry-aware ranking, explainable "
        "urgency classification, restock and duplicate-purchase detection.<br/><br/>"
        "<b>Stack:</b> Python, Streamlit, SQLite, pandas, scikit-learn, Plotly.<br/><br/>"
        "<b>Data:</b> recipes are a project-curated dataset (see docs/DATA_ATTRIBUTION.md). "
        "Sample inventory is bundled for demo purposes.<br/><br/>"
        "<b>Safety:</b> expiry dates are labels, not safety verdicts. For use-by dates, "
        "always follow the package instructions and local food-safety guidance.</div>"
    )
