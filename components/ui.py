"""Shared UI primitives: cards, badges, headers, empty states, CSS."""

from __future__ import annotations

import streamlit as st

APP_CSS = """
<style>
:root { --wl-green:#1B7A43; --wl-green-dark:#145c33; --wl-cream:#FAF7F2;
        --wl-ink:#1F2A24; --wl-muted:#6B7280; --wl-red:#B3261E;
        --wl-orange:#D35400; --wl-amber:#B8860B; }
.stApp { background: var(--wl-cream); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0F3D24 0%,#145c33 100%);
    color: #EAF5EE;
}
section[data-testid="stSidebar"] * { color: #EAF5EE !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 2px; }
section[data-testid="stSidebar"] label { font-weight: 500; }

/* Cards */
.wl-card { background:#fff; border:1px solid #E7E2D8; border-radius:14px;
  padding:18px 20px; margin-bottom:14px; box-shadow:0 1px 3px rgba(31,42,36,.06); }
.wl-card h4 { margin:0 0 4px 0; color:var(--wl-ink); font-size:1.02rem; }
.wl-card .wl-sub { color:var(--wl-muted); font-size:.85rem; }
.wl-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:14px; margin-bottom:14px; }
.wl-metric { background:#fff; border:1px solid #E7E2D8; border-radius:14px;
  padding:16px 18px; box-shadow:0 1px 3px rgba(31,42,36,.06); }
.wl-metric .wl-value { font-size:1.7rem; font-weight:700; color:var(--wl-ink);
  line-height:1.1; }
.wl-metric .wl-label { font-size:.82rem; color:var(--wl-muted); margin-top:2px; }
.wl-metric .wl-delta { font-size:.78rem; margin-top:4px; }

/* Badges */
.wl-badge { display:inline-block; padding:2px 10px; border-radius:999px;
  font-size:.75rem; font-weight:600; letter-spacing:.02em; }
.wl-badge.expired { background:#FDECEA; color:#B3261E; }
.wl-badge.critical { background:#FDECEA; color:#C0392B; }
.wl-badge.high { background:#FDF0E4; color:#D35400; }
.wl-badge.medium { background:#FBF3DC; color:#8a6d1a; }
.wl-badge.ok { background:#E5F4EA; color:#1B7A43; }
.wl-badge.none { background:#EEF0F2; color:#6B7280; }
.wl-badge.info { background:#E8F0FE; color:#1a56db; }

/* Headers */
.wl-title { font-size:1.9rem; font-weight:800; color:var(--wl-ink);
  letter-spacing:-.02em; margin-bottom:2px; }
.wl-subtitle { color:var(--wl-muted); font-size:.95rem; margin-bottom:18px; }

/* Info / warning boxes */
.wl-note { border-left:4px solid var(--wl-green); background:#fff;
  border-radius:0 10px 10px 0; padding:12px 16px; margin:10px 0;
  font-size:.88rem; color:#33413a; }
.wl-note.warn { border-color:#D35400; background:#FDF6EE; }
.wl-note.danger { border-color:#B3261E; background:#FDF0EF; }
.wl-note.info { border-color:#1a56db; background:#EFF6FF; }

/* Buttons */
.stButton > button { border-radius:10px !important; font-weight:600 !important;
  transition: transform .08s ease, box-shadow .15s ease; }
.stButton > button:hover { transform: translateY(-1px);
  box-shadow:0 4px 12px rgba(20,92,51,.18) !important; }

/* Tables */
.wl-table { width:100%; border-collapse:collapse; font-size:.88rem; }
.wl-table th { text-align:left; padding:8px 10px; color:var(--wl-muted);
  font-size:.75rem; text-transform:uppercase; letter-spacing:.05em;
  border-bottom:1px solid #E7E2D8; }
.wl-table td { padding:9px 10px; border-bottom:1px solid #F0EBE1;
  color:var(--wl-ink); }
.wl-table tr:hover td { background:#FAF8F3; }

/* Misc */
.wl-empty { text-align:center; padding:48px 20px; color:var(--wl-muted); }
.wl-empty .wl-empty-icon { font-size:2.6rem; margin-bottom:8px; }
.wl-section-label { font-size:.75rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.08em; color:var(--wl-muted); margin:22px 0 10px 2px; }
.exp-bar { height:6px; border-radius:3px; background:#EDE8DE; overflow:hidden; }
.exp-bar > div { height:100%; border-radius:3px; }
</style>
"""


def inject_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="wl-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="wl-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "info") -> str:
    return f'<span class="wl-badge {kind}">{text}</span>'


def badge_html(text: str, kind: str = "info") -> None:
    st.markdown(badge(text, kind), unsafe_allow_html=True)


def metric_cards(metrics: list[dict]) -> None:
    """metrics: [{value, label, delta?, delta_kind?}]"""
    cards = "".join(
        f'''<div class="wl-metric">
              <div class="wl-value">{m["value"]}</div>
              <div class="wl-label">{m["label"]}</div>
              {f'<div class="wl-delta" style="color:{"#1B7A43" if m.get("delta_kind")=="good" else "#B3261E" if m.get("delta_kind")=="bad" else "#6B7280"}">{m["delta"]}</div>' if m.get("delta") else ""}
            </div>'''
        for m in metrics
    )
    st.markdown(f'<div class="wl-grid">{cards}</div>', unsafe_allow_html=True)


def card(title: str, body_html: str, subtitle: str = "") -> None:
    sub = f'<div class="wl-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="wl-card"><h4>{title}</h4>{sub}{body_html}</div>',
        unsafe_allow_html=True,
    )


def note(text: str, kind: str = "info") -> None:
    st.markdown(f'<div class="wl-note {kind}">{text}</div>', unsafe_allow_html=True)


def empty_state(icon: str, title: str, hint: str = "", action_label: str = "",
                action_key: str = "") -> None:
    st.markdown(
        f'<div class="wl-empty"><div class="wl-empty-icon">{icon}</div>'
        f'<div style="font-weight:600;color:#1F2A24">{title}</div>'
        f'<div style="font-size:.85rem;margin-top:4px">{hint}</div></div>',
        unsafe_allow_html=True,
    )
    if action_label and action_key:
        if st.button(action_label, key=action_key, use_container_width=True):
            st.session_state["pending_action"] = action_key


def section_label(text: str) -> None:
    st.markdown(f'<div class="wl-section-label">{text}</div>', unsafe_allow_html=True)


def urgency_badge(urgency: str) -> str:
    meta = {
        "expired": ("Expired", "expired"),
        "critical": ("Use today", "critical"),
        "high": ("Expiring soon", "high"),
        "medium": ("Plan to use", "medium"),
        "ok": ("Fresh", "ok"),
        "none": ("No date", "none"),
    }.get(urgency, (urgency, "none"))
    return badge(meta[0], meta[1])


def progress_bar(pct: float, color: str = "#1B7A43") -> str:
    pct = max(0.0, min(100.0, pct))
    return (f'<div class="exp-bar"><div style="width:{pct}%;background:{color}"></div></div>')


def fmt_money(v) -> str:
    if v is None:
        return "—"
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return "—"
