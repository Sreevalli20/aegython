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
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700;800&display=swap');
:root {
  --wl-green:#1E5B3A; --wl-green-dark:#123C26; --wl-pine:#0E2A1C;
  --wl-sage:#A9C3A4; --wl-sage-soft:#E4EDE0; --wl-gold:#C19A3D;
  --wl-gold-soft:#F4ECD8; --wl-ivory:#FAF6EE; --wl-paper:#FFFFFF;
  --wl-ink:#212A23; --wl-muted:#71806F; --wl-line:#E9E2D2;
  --wl-red:#B3261E; --wl-orange:#D35400; --wl-amber:#9A7B12;
}
.stApp { background: var(--wl-ivory); }
html, body, [data-testid="stAppViewContainer"], .main, [data-testid="stMain"] {
  font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif !important;
}
h1,h2,h3,h4,.wl-title,.wl-brand,.wl-serif { font-family:'Fraunces',Georgia,'Times New Roman',serif !important; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: linear-gradient(178deg,#0D2718 0%,#134A2C 55%,#1E5B3A 100%);
  border-right:1px solid rgba(193,154,61,.25);
}
section[data-testid="stSidebar"] * { color:#E9F2EA !important; }
section[data-testid="stSidebar"] .stRadio > div { gap:6px; }
section[data-testid="stSidebar"] label { font-weight:500; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
  padding:10px 14px; border-radius:12px; margin:2px 0;
  font-size:.92rem; letter-spacing:.01em;
  transition:background .15s ease, transform .1s ease;
  display:flex; align-items:center;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background:rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background:linear-gradient(90deg, rgba(193,154,61,.28), rgba(169,195,164,.16));
  box-shadow:inset 3px 0 0 #D9B45B;
  font-weight:700;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color:#D9B45B; }
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button { color:#E9F2EA !important; }

/* ---------- Brand / topbar ---------- */
.wl-topbar { display:flex; align-items:center; justify-content:space-between;
  gap:16px; padding:14px 6px 18px 6px; border-bottom:1px solid var(--wl-line);
  margin-bottom:22px; }
.wl-topbar .wl-brand { font-family:'Fraunces',Georgia,serif; font-size:1.35rem;
  font-weight:700; letter-spacing:-.01em; color:var(--wl-ink); }
.wl-topbar .wl-brand em { font-style:normal; color:var(--wl-green); }
.wl-topbar .wl-meta { font-size:.8rem; color:var(--wl-muted); text-align:right;
  line-height:1.5; }
.wl-topbar .wl-meta b { color:var(--wl-green); font-weight:700; }

/* ---------- Cards ---------- */
.wl-card { background:var(--wl-paper); border:1px solid var(--wl-line);
  border-radius:16px; padding:20px 22px; margin-bottom:14px;
  box-shadow:0 1px 2px rgba(33,42,35,.05), 0 8px 24px -18px rgba(33,42,35,.25);
  transition:box-shadow .18s ease, transform .18s ease; }
.wl-card:hover { box-shadow:0 2px 4px rgba(33,42,35,.06), 0 14px 30px -18px rgba(30,91,58,.35); }
.wl-card h4 { margin:0 0 4px 0; color:var(--wl-ink); font-size:1.05rem;
  font-family:'Fraunces',Georgia,serif; font-weight:600; }
.wl-card .wl-sub { color:var(--wl-muted); font-size:.85rem; }
.wl-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:16px; margin-bottom:18px; }
.wl-metric { background:var(--wl-paper); border:1px solid var(--wl-line);
  border-radius:16px; padding:18px 20px; position:relative; overflow:hidden;
  box-shadow:0 1px 2px rgba(33,42,35,.05); }
.wl-metric::before { content:""; position:absolute; top:0; left:0; right:0;
  height:3px; background:linear-gradient(90deg,var(--wl-green),var(--wl-gold)); }
.wl-metric .wl-metric-top { display:flex; align-items:center; gap:10px; }
.wl-metric .wl-icon { width:34px; height:34px; border-radius:10px;
  display:flex; align-items:center; justify-content:center; font-size:1rem;
  background:var(--wl-sage-soft); }
.wl-metric .wl-value { font-family:'Fraunces',Georgia,serif; font-size:1.85rem;
  font-weight:700; color:var(--wl-ink); line-height:1.05; margin-top:8px; }
.wl-metric .wl-label { font-size:.8rem; color:var(--wl-muted); margin-top:2px;
  font-weight:500; }
.wl-metric .wl-delta { font-size:.78rem; margin-top:5px; font-weight:600; }

/* ---------- Badges ---------- */
.wl-badge { display:inline-block; padding:3px 11px; border-radius:999px;
  font-size:.74rem; font-weight:600; letter-spacing:.02em; white-space:nowrap; }
.wl-badge.expired { background:#FDECEA; color:#B3261E; }
.wl-badge.critical { background:#FDECEA; color:#C0392B; }
.wl-badge.high { background:#FDF0E4; color:#D35400; }
.wl-badge.medium { background:#FBF3DC; color:#8a6d1a; }
.wl-badge.ok { background:#E5F4EA; color:#1E5B3A; }
.wl-badge.none { background:#EEF0F2; color:#6B7280; }
.wl-badge.info { background:#E8F0FE; color:#1a56db; }
.wl-badge.gold { background:var(--wl-gold-soft); color:#8a6d1a; }

/* ---------- Headers ---------- */
.wl-title { font-family:'Fraunces',Georgia,serif; font-size:2rem;
  font-weight:700; color:var(--wl-ink); letter-spacing:-.015em; margin-bottom:4px; }
.wl-subtitle { color:var(--wl-muted); font-size:.95rem; margin-bottom:20px; }

/* ---------- Notes ---------- */
.wl-note { border-left:4px solid var(--wl-green); background:#fff;
  border-radius:0 12px 12px 0; padding:13px 17px; margin:12px 0;
  font-size:.88rem; color:#33413a; }
.wl-note.warn { border-color:#D35400; background:#FDF6EE; }
.wl-note.danger { border-color:#B3261E; background:#FDF0EF; }
.wl-note.info { border-color:#2B6CB0; background:#EFF6FF; }
.wl-note.gold { border-color:var(--wl-gold); background:var(--wl-gold-soft); }

/* ---------- Buttons / inputs ---------- */
.stButton > button { border-radius:11px !important; font-weight:600 !important;
  transition:transform .08s ease, box-shadow .15s ease, background .15s ease; }
.stButton > button:hover { transform:translateY(-1px);
  box-shadow:0 6px 16px rgba(30,91,58,.22) !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#1E5B3A,#2E7D4F) !important;
  border:none !important; }
[data-testid="stFormSubmitButton"] button { border-radius:11px !important;
  font-weight:700 !important; }
input, textarea, select, .stSelectbox, .stTextInput, .stNumberInput,
.stDateInput, .stSlider { border-radius:10px !important; }

/* ---------- Tables ---------- */
.wl-table { width:100%; border-collapse:collapse; font-size:.88rem; }
.wl-table th { text-align:left; padding:9px 12px; color:var(--wl-muted);
  font-size:.72rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.07em; border-bottom:1px solid var(--wl-line); }
.wl-table td { padding:10px 12px; border-bottom:1px solid #F1EBDD;
  color:var(--wl-ink); }
.wl-table tr:hover td { background:#FBF8F1; }

/* ---------- Action rows ---------- */
.wl-empty { text-align:center; padding:52px 20px; color:var(--wl-muted); }
.wl-empty .wl-empty-icon { font-size:3rem; margin-bottom:10px;
  filter:drop-shadow(0 4px 10px rgba(30,91,58,.25)); }
.wl-section-label { font-family:'Fraunces',Georgia,serif; font-size:.95rem;
  font-weight:700; color:var(--wl-green-dark); margin:26px 0 12px 2px;
  display:flex; align-items:center; gap:8px; }
.wl-section-label::after { content:""; flex:1; height:1px;
  background:linear-gradient(90deg,var(--wl-line),transparent); }
.wl-action-row { display:flex; align-items:center; justify-content:space-between;
  gap:10px; padding:13px 18px; margin-bottom:8px; }
.wl-action-row .wl-action-text { font-size:.88rem; color:#33413a; }
.wl-action-row .wl-action-icon { width:36px; height:36px; border-radius:10px;
  display:flex; align-items:center; justify-content:center; font-size:1rem;
  flex-shrink:0; }
.exp-bar { height:7px; border-radius:4px; background:#EDE8DE; overflow:hidden; }
.exp-bar > div { height:100%; border-radius:4px; }

/* ---------- Recipe / photo cards ---------- */
.wl-photo-card { border-radius:14px; overflow:hidden; position:relative;
  background:linear-gradient(135deg,#1E5B3A,#3E7C59); min-height:150px;
  display:flex; align-items:flex-end; }
.wl-photo-card img { position:absolute; inset:0; width:100%; height:100%;
  object-fit:cover; }
.wl-photo-card .wl-photo-fallback { position:absolute; inset:0; display:flex;
  align-items:center; justify-content:center; font-size:2.6rem;
  color:rgba(255,255,255,.85); }
.wl-photo-card .wl-photo-cap { position:relative; z-index:2; width:100%;
  padding:14px 16px; background:linear-gradient(180deg,transparent,rgba(10,25,16,.78));
  color:#fff; }
.wl-recipe-card { display:grid; grid-template-columns:150px 1fr; gap:0;
  overflow:hidden; align-items:stretch; }
.wl-recipe-card .wl-recipe-photo { min-height:130px; }
.wl-recipe-card .wl-recipe-body { padding:16px 18px; }
@media (max-width:640px){ .wl-recipe-card{ grid-template-columns:1fr; } .wl-recipe-card .wl-recipe-photo{ min-height:110px; } }

/* ---------- Chips ---------- */
.wl-chip { display:inline-flex; align-items:center; gap:5px; padding:4px 11px;
  border-radius:999px; background:var(--wl-sage-soft); color:#2F5238;
  font-size:.78rem; font-weight:600; margin:2px 4px 2px 0; }
.wl-chip.gold { background:var(--wl-gold-soft); color:#7A5E14; }
.wl-chip.red { background:#FDECEA; color:#B3261E; }

/* ---------- Progress ring-ish stat ---------- */
.wl-stat-pair { display:flex; gap:14px; align-items:center; }

/* ---------- Dataframe polish ---------- */
[data-testid="stDataFrame"] { border:1px solid var(--wl-line) !important;
  border-radius:12px !important; overflow:hidden; }
[data-testid="stMetricValue"] { font-family:'Fraunces',Georgia,serif !important; }

/* ---------- Tabs ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:6px; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius:10px 10px 0 0 !important;
  font-weight:600 !important; }
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
    """metrics: [{value, label, delta?, delta_kind?, icon?}]

    Each card is emitted as a single line so the markup contains no blank
    lines — required for the markdown fallback path to stay intact.
    """
    cards = []
    for m in metrics:
        delta = ""
        if m.get("delta"):
            color = {"good": "#1E5B3A", "bad": "#B3261E"}.get(
                m.get("delta_kind"), "#6B7280")
            delta = (f'<div class="wl-delta" style="color:{color}">'
                     f'{esc(m["delta"])}</div>')
        icon = ""
        if m.get("icon"):
            icon = f'<div class="wl-icon">{m["icon"]}</div>'
        top = f'<div class="wl-metric-top">{icon}</div>' if icon else ""
        cards.append(
            f'<div class="wl-metric">{top}'
            f'<div class="wl-value">{esc(m["value"])}</div>'
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
        f'<div style="font-weight:700;font-size:1.05rem;color:#212A23;'
        f'font-family:Fraunces,Georgia,serif">{esc(title)}</div>'
        f'<div style="font-size:.87rem;margin-top:6px">{esc(hint)}</div></div>'
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


def progress_bar(pct: float, color: str = "#1E5B3A") -> str:
    pct = max(0.0, min(100.0, pct))
    return (f'<div class="exp-bar"><div style="width:{pct}%;background:{color}"></div></div>')


def action_row(icon: str, text_html: str, color: str = "#1E5B3A") -> str:
    """A single-line action row for plan-style lists."""
    return (
        f'<div class="wl-card wl-action-row" style="border-left:4px solid {color};'
        f'padding:13px 18px;margin-bottom:8px">'
        f'<span class="wl-action-icon" style="background:{color}1A">{icon}</span>'
        f'<span class="wl-action-text">{text_html}</span></div>'
    )


def chip(text: str, kind: str = "") -> str:
    return f'<span class="wl-chip {kind}">{esc(text)}</span>'


def photo_block(url: str, emoji: str = "🍽️", caption: str = "",
                height: int = 150) -> str:
    """Image with graceful emoji/gradient fallback if the photo fails."""
    cap = ""
    if caption:
        cap = f'<div class="wl-photo-cap"><b>{esc(caption)}</b></div>'
    return (
        f'<div class="wl-photo-card" style="min-height:{height}px">'
        f'<div class="wl-photo-fallback">{emoji}</div>'
        f'<img src="{esc(url)}" alt="{esc(caption or emoji)}" loading="lazy" '
        f'onerror="this.remove()"/>{cap}</div>'
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


def days_left_cell(days) -> object:
    """Safe value for a 'Days left' dataframe column.

    Returns a nullable integer so pandas never sees a bare '—' string mixed
    into a numeric column (the previous source of the dtype error).
    """
    if days is None:
        return None
    try:
        return int(days)
    except (TypeError, ValueError):
        return None
