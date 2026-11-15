"""Settings & About — data management, privacy, attribution."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from components import ui
from src import database, inventory


def render(db_path=None) -> None:
    ui.page_header("Settings & About", "Data, privacy and app information.")

    path = Path(db_path) if db_path else database.DEFAULT_DB_PATH

    ui.section_label("Local data")
    st.markdown(
        '<div class="wl-card"><b>Streamlit Cloud storage:</b> the repository is '
        'read-only and SQLite files are ephemeral by default. Data can reset on '
        'redeploy or instance replacement. Set <code>WASTELESS_DB_PATH</code> to a '
        'mounted persistent volume for production persistence.<br/><br/>'
        f'<b>Storage:</b> SQLite database at <code>{path}</code><br/>'
        f'<b>Contents:</b> your pantry items, consumption/waste log, shopping list.<br/>'
        f'<b>Privacy:</b> everything stays on this device. No accounts, no cloud sync, '
        f'no external AI APIs, no analytics beacons.<br/><br/>'
        '<b>Recommendation:</b> for a hackathon demo, local SQLite is sufficient. '
        'For real household persistence on Streamlit Cloud, attach persistent storage '
        'and set WASTELESS_DB_PATH to that mounted path.</div>',
        unsafe_allow_html=True,
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
    st.markdown(
        '<div class="wl-card"><b>WasteLess AI</b> — an offline-first household food '
        "waste prevention platform.<br/><br/>"
        "<b>Intelligence:</b> TF-IDF + cosine-similarity recipe matching, "
        "IDF-weighted ingredient coverage, expiry-aware ranking, explainable "
        "urgency classification, restock and duplicate-purchase detection.<br/><br/>"
        "<b>Stack:</b> Python, Streamlit, SQLite, pandas, scikit-learn, Plotly.<br/><br/>"
        "<b>Data:</b> recipes are a project-curated dataset (see docs/DATA_ATTRIBUTION.md). "
        "Sample inventory is bundled for demo purposes.<br/><br/>"
        "<b>Safety:</b> expiry dates are labels, not safety verdicts. For use-by dates, "
        "always follow the package instructions and local food-safety guidance.</div>",
        unsafe_allow_html=True,
    )
