"""Shared UI primitives: cards, badges, headers, empty states, CSS.

All raw-HTML rendering goes through :func:`raw_html`, which prefers
``st.html`` (no markdown parsing at all) and falls back to
``st.markdown(unsafe_allow_html=True)`` on older Streamlit versions.
HTML fragments are always emitted without blank lines so the markdown
fallback can never split an HTML block into visible text.
"""

from __future__ import annotations

import html as _html
import re

import streamlit as st

APP_CSS = """
<style>
:root { --wl-green:#1B7A43; --wl-green-dark:#145c33; --wl-cream:#FAF7F2;
        --wl-ink:#1F2A24; --wl-muted:#6B7280; --wl-red:#B3261E;
        --wl-orange:#D35400; --wl-amber:#B8860B; }
.stApp { background: var(--wl-cream); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0C2E1B 0%,#145c33 100%);
    color: #EAF5EE;
}
section[data-testid="stSidebar"] * { color: #EAF5EE !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
section[data-testid="stSidebar"] label { font-weight: 500; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 7px 12px; border-radius: 9px; margin: 1px 0;
    transition: background .12s ease;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(127,214,164,.18);
    box-shadow: inset 3px 0 0 #7FD6A4;
    font-weight: 700;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color: #7FD6A4; }

/* Top brand bar */
.wl-topbar { display:flex; align-items:center; justify-content:space-between;
  gap:16px; padding:10px 4px 14px 4px; border-bottom:1px solid #E7E2D8;
  margin-bottom:18px; }
.wl-topbar .wl-brand { font-size:1.15rem; font-weight:800; letter-spacing:-.02em;
  color:var(--wl-ink); }
.wl-topbar .wl-brand span { color:var(--wl-green); }
.wl-topbar .wl-meta { font-size:.78rem; color:var(--wl-muted); text-align:right; }

/* Cards */
.wl-card { background:#fff; border:1px solid #E7E2D8; border-radius:14px;
  padding:18px 20px; margin-bottom:14px; box-shadow:0 1px 3px rgba(31,42,36,.06); }
.wl-card h4 { margin:0 0 4px 0; color:var(--wl-ink); font-size:1.02rem; }
.wl-card .wl-sub { color:var(--wl-muted); font-size:.85rem; }
.wl-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:14px; margin-bottom:14px; }
.wl-metric { background:#fff; border:1px solid #E7E2D8; border-radius:14px;
  padding:16px 18px; box-shadow:0 1px 3px rgba(31,42,36,.06);
  border-top:3px solid #1B7A43; }
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
.wl-action-row { display:flex; align-items:center; justify-content:space-between;
  gap:10px; padding:11px 16px; margin-bottom:8px; }
.wl-action-row .wl-action-text { font-size:.88rem; color:#33413a; }
.exp-bar { height:6px; border-radius:3px; background:#EDE8DE; overflow:hidden; }
.exp-bar > div { height:100%; border-radius:3px; }

/* Dataframe polish */
[data-testid="stDataFrame"] { border:1px solid #E7E2D8 !important;
  border-radius:12px !important; overflow:hidden; }
</style>
"""

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def raw_html(body: str) -> None:
    """Render an HTML fragment safely.

    Uses ``st.html`` when available (Streamlit >= 1.55-ish) so the markup is
    never passed through the markdown parser. The fallback keeps every
    fragment free of blank lines, which is what previously caused raw HTML
    to leak into the page as text.
    """
    if hasattr(st, "html"):
        st.html(body)
    else:  # pragma: no cover - older Streamlit fallback
        st.markdown(body, unsafe_allow_html=True)


def esc(value) -> str:
    """Escape a user-supplied string for safe interpolation into HTML."""
    return _html.escape(str(value), quote=True)


def inject_css() -> None:
    raw_html(APP_CSS)


def page_header(title: str, subtitle: str = "") -> None:
    raw_html(f'<div class="wl-title">{esc(title)}</div>')
    if subtitle:
        raw_html(f'<div class="wl-subtitle">{esc(subtitle)}</div>')


def badge(text: str, kind: str = "info") -> str:
    return f'<span class="wl-badge {kind}">{esc(text)}</span>'


def badge_html(text: str, kind: str = "info") -> None:
    raw_html(badge(text, kind))


def metric_cards(metrics: list[dict]) -> None:
    """metrics: [{value, label, delta?, delta_kind?}]

    Each card is emitted as a single line so the markup contains no blank
    lines — required for the markdown fallback path to stay intact.
    """
    cards = []
    for m in metrics:
        delta = ""
        if m.get("delta"):
            color = {"good": "#1B7A43", "bad": "#B3261E"}.get(
                m.get("delta_kind"), "#6B7280")
            delta = (f'<div class="wl-delta" style="color:{color}">'
                     f'{esc(m["delta"])}</div>')
        cards.append(
            f'<div class="wl-metric"><div class="wl-value">{esc(m["value"])}</div>'
            f'<div class="wl-label">{esc(m["label"])}</div>{delta}</div>'
        )
    raw_html('<div class="wl-grid">' + "".join(cards) + "</div>")


def card(title: str, body_html: str, subtitle: str = "") -> None:
    sub = f'<div class="wl-sub">{esc(subtitle)}</div>' if subtitle else ""
    raw_html(
        f'<div class="wl-card"><h4>{esc(title)}</h4>{sub}{body_html}</div>'
    )


def note(text: str, kind: str = "info") -> None:
    """Info/warning box. Supports ``**bold**`` markdown-lite and escapes HTML."""
    safe = esc(text)
    safe = _BOLD_RE.sub(r"<b>\1</b>", safe)
    raw_html(f'<div class="wl-note {kind}">{safe}</div>')


def empty_state(icon: str, title: str, hint: str = "", action_label: str = "",
                action_key: str = "") -> None:
    raw_html(
        f'<div class="wl-empty"><div class="wl-empty-icon">{icon}</div>'
        f'<div style="font-weight:600;color:#1F2A24">{esc(title)}</div>'
        f'<div style="font-size:.85rem;margin-top:4px">{esc(hint)}</div></div>'
    )
    if action_label and action_key:
        if st.button(action_label, key=action_key, width="content"):
            st.session_state["pending_action"] = action_key


def section_label(text: str) -> None:
    raw_html(f'<div class="wl-section-label">{esc(text)}</div>')


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


def urgency_label(urgency: str) -> str:
    """Plain-text label for dataframe cells."""
    return {
        "expired": "Expired", "critical": "Use today",
        "high": "Expiring soon", "medium": "Plan to use",
        "ok": "Fresh", "none": "No date",
    }.get(urgency, urgency or "—")


def progress_bar(pct: float, color: str = "#1B7A43") -> str:
    pct = max(0.0, min(100.0, pct))
    return (f'<div class="exp-bar"><div style="width:{pct}%;background:{color}"></div></div>')


def action_row(icon: str, text_html: str, color: str = "#1B7A43") -> str:
    """A single-line action row for plan-style lists."""
    return (
        f'<div class="wl-card wl-action-row" style="border-left:4px solid {color};'
        f'padding:11px 16px;margin-bottom:8px">'
        f'<span style="margin-right:8px">{icon}</span>'
        f'<span class="wl-action-text">{text_html}</span></div>'
    )


def navigate(page_key: str) -> None:
    """Request navigation to another page on the next rerun.

    Sets both the logical page and a jump flag; app.py clears the flag and
    resets the radio widget so the selection actually changes.
    """
    st.session_state["nav"] = page_key
    st.session_state["_nav_jump"] = True


def fmt_money(v) -> str:
    if v is None:
        return "—"
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return "—"
