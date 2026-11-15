"""WasteLess AI — Streamlit entrypoint.

Run:  streamlit run app.py
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from components import ui  # noqa: E402
from src import database  # noqa: E402

log = logging.getLogger(__name__)

st.set_page_config(
    page_title="WasteLess AI",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# (key, label, icon) — single source of truth for navigation.
NAV = [
    ("dashboard", "Dashboard", "🏠"),
    ("pantry", "My Pantry", "🥫"),
    ("expiry", "Expiry Intelligence", "⏳"),
    ("meals", "Discover Meals", "🍽️"),
    ("waste", "Waste Prevention", "♻️"),
    ("shopping", "Shopping List", "🛒"),
    ("analytics", "Analytics", "📊"),
    ("simulator", "What-if Simulator", "🧪"),
    ("settings", "Settings", "⚙️"),
]
NAV_LABELS = {k: label for k, label, _ in NAV}
NAV_ICONS = {k: icon for k, _, icon in NAV}

ui.inject_css()
try:
    database.init_db()
except Exception as exc:  # storage unavailable — friendly message, no traceback
    log.exception("WasteLess AI could not open its local database")
    st.error(
        "WasteLess AI could not open its local database. The app cannot store "
        "pantry, shopping, or activity data until storage is available."
    )
    st.stop()

# --- Sidebar navigation (the ONLY navigation system in the app) ------------
with st.sidebar:
    ui.raw_html(
        '<div style="padding:4px 4px 16px 4px">'
        '<div style="font-size:1.45rem;font-weight:800;letter-spacing:-.02em">'
        'WasteLess <span style="color:#7FD6A4">AI</span></div>'
        '<div style="font-size:.78rem;opacity:.75;margin-top:2px">'
        'Know what you have. Waste less.</div></div>'
    )

    keys = [k for k, _, _ in NAV]
    if "nav" not in st.session_state or st.session_state["nav"] not in keys:
        st.session_state["nav"] = "dashboard"

    if st.session_state.pop("_nav_jump", False):
        # A page requested navigation programmatically — reset the radio
        # widget so it adopts the requested selection instead of its old one.
        st.session_state.pop("nav_radio", None)

    choice = st.radio(
        "Navigate", keys, index=keys.index(st.session_state["nav"]),
        format_func=lambda k: f"{NAV_ICONS[k]}  {NAV_LABELS[k]}",
        label_visibility="collapsed", key="nav_radio",
    )
    st.session_state["nav"] = choice

    ui.raw_html(
        '<div style="position:absolute;bottom:14px;left:18px;font-size:.72rem;opacity:.6">'
        'Offline-first · SQLite · Runs locally</div>'
    )

# --- Brand header -----------------------------------------------------------
ui.raw_html(
    '<div class="wl-topbar">'
    '<div class="wl-brand">WasteLess <span>AI</span></div>'
    '<div class="wl-meta">'
    f'{date.today().strftime("%A, %d %B %Y")}<br/>'
    'Your kitchen, minus the waste</div></div>'
)

# --- Route -----------------------------------------------------------------
page = st.session_state["nav"]

try:
    if page == "dashboard":
        from views import dashboard
        dashboard.render()
    elif page == "pantry":
        from views import pantry
        pantry.render()
    elif page == "expiry":
        from views import expiry
        expiry.render()
    elif page == "meals":
        from views import meals
        meals.render()
    elif page == "waste":
        from views import waste
        waste.render()
    elif page == "shopping":
        from views import shopping
        shopping.render()
    elif page == "analytics":
        from views import analytics
        analytics.render()
    elif page == "simulator":
        from views import simulator
        simulator.render()
    elif page == "settings":
        from views import settings
        settings.render()
    else:
        st.error("Unknown page.")
except sqlite3.Error as exc:
    log.exception("database error while rendering %s", page)
    st.error(
        "WasteLess AI could not access the local database. Your existing data "
        "was not deleted; try again after storage becomes available."
    )
except (ValueError, KeyError, TypeError) as exc:
    log.exception("render error on %s", page)
    st.error(
        "WasteLess AI could not complete that action because the stored data "
        "needs attention."
    )
