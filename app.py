"""WasteLess AI — Streamlit entrypoint.

Run:  streamlit run app.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from components import ui  # noqa: E402
from src import database  # noqa: E402

st.set_page_config(
    page_title="WasteLess AI",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV = [
    ("dashboard", "Home Dashboard"),
    ("pantry", "My Pantry"),
    ("expiry", "Expiry Intelligence"),
    ("meals", "Discover Meals"),
    ("waste", "Waste Prevention"),
    ("shopping", "Shopping List"),
    ("analytics", "Analytics"),
    ("simulator", "What-if Simulator"),
    ("settings", "Settings & About"),
]

ui.inject_css()
try:
    database.init_db()
except Exception as exc:
    st.error(
        "WasteLess AI could not open its local database. The app cannot store pantry, "
        "shopping, or activity data until storage is available."
    )
    st.exception(exc)
    st.stop()

# --- Sidebar navigation ----------------------------------------------------
with st.sidebar:
    st.caption(
        "Temporary local storage can reset when Streamlit Cloud replaces the instance. "
        "Set WASTELESS_DB_PATH to persistent storage for production use."
    )
    st.markdown(
        '<div style="padding:6px 4px 14px 4px">'
        '<div style="font-size:1.35rem;font-weight:800;letter-spacing:-.02em">'
        'WasteLess <span style="color:#7FD6A4">AI</span></div>'
        '<div style="font-size:.78rem;opacity:.75;margin-top:2px">'
        'Know what you have. Waste less.</div></div>',
        unsafe_allow_html=True,
    )
    keys = [k for k, _ in NAV]
    if "nav" not in st.session_state or st.session_state["nav"] not in keys:
        st.session_state["nav"] = "dashboard"
    choice = st.radio(
        "Navigate", keys, index=keys.index(st.session_state["nav"]),
        format_func=lambda k: dict(NAV)[k],
        label_visibility="collapsed", key="nav_radio",
    )
    st.session_state["nav"] = choice
    st.markdown(
        '<div style="position:absolute;bottom:14px;left:18px;font-size:.72rem;opacity:.6">'
        'Offline-first · SQLite · No external AI APIs</div>',
        unsafe_allow_html=True,
    )

# --- Route -----------------------------------------------------------------
page = st.session_state["nav"]

try:
    if page == "dashboard":
        from pages import dashboard
        dashboard.render()
    elif page == "pantry":
        from pages import pantry
        pantry.render()
    elif page == "expiry":
        from pages import expiry
        expiry.render()
    elif page == "meals":
        from pages import meals
        meals.render()
    elif page == "waste":
        from pages import waste
        waste.render()
    elif page == "shopping":
        from pages import shopping
        shopping.render()
    elif page == "analytics":
        from pages import analytics
        analytics.render()
    elif page == "simulator":
        from pages import simulator
        simulator.render()
    elif page == "settings":
        from pages import settings
        settings.render()
    else:
        st.error("Unknown page.")
except sqlite3.Error as exc:
    st.error("WasteLess AI could not access the local database. Your existing data was not deleted; try again after storage becomes available.")
    st.exception(exc)
except (ValueError, KeyError, TypeError) as exc:
    st.error("WasteLess AI could not complete that action because the stored data needs attention.")
    st.exception(exc)
