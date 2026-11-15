"""Plotly chart helpers — all charts render real application data."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "bg": "#FAF7F2", "paper": "#FFFFFF", "ink": "#1F2A24",
    "grid": "#EDE8DE", "green": "#1B7A43", "red": "#B3261E",
    "orange": "#D35400", "amber": "#B8860B", "blue": "#2B6CB0",
    "teal": "#0E7490", "purple": "#6D28D9", "gray": "#6B7280",
}

LAYOUT_BASE = dict(
    paper_bgcolor=COLORS["paper"], plot_bgcolor=COLORS["paper"],
    font=dict(color=COLORS["ink"], size=12),
    margin=dict(l=40, r=16, t=30, b=36),
    xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
    yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
    legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11)),
)


def _apply_layout(fig, **kw):
    layout = {**LAYOUT_BASE, **kw}
    fig.update_layout(**layout)
    return fig


def urgency_donut(summary: dict, key: str = "urgency_donut") -> None:
    """Expiry urgency distribution donut."""
    labels = ["Expired", "Use today", "Expiring soon", "Plan to use", "Fresh", "No date"]
    values = [
        summary.get("expired", 0), summary.get("critical", 0),
        summary.get("high", 0), summary.get("medium", 0),
        summary.get("ok", 0), summary.get("none", 0),
    ]
    colors = ["#B3261E", "#C0392B", "#D35400", "#B8860B", "#1B7A43", "#9CA3AF"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=colors, line=dict(color="#fff", width=2)),
        textinfo="label+percent", textfont=dict(size=11),
        sort=False,
    ))
    fig.update_layout(
        title=dict(text=f"{summary.get('total', 0)} tracked items", font=dict(size=14)),
        showlegend=False, margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def daily_waste_trend(series: list[dict], key: str = "daily_trend") -> None:
    """Consumed vs wasted quantities over recent days."""
    if not series:
        return
    df = pd.DataFrame(series)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(30)
    fig = px.line(
        df, x="date", y=["consumed", "wasted"],
        labels={"value": "Quantity", "date": "", "variable": "Event"},
        color_discrete_map={"consumed": COLORS["green"], "wasted": COLORS["red"]},
        markers=True,
    )
    _apply_layout(fig, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=key)


def category_waste_chart(rows: list[dict], key: str = "cat_waste") -> None:
    """Wasted quantity by category."""
    df = pd.DataFrame([r for r in rows if r.get("wasted_qty", 0) > 0])
    if df.empty:
        return
    df = df.sort_values("wasted_qty", ascending=True).tail(8)
    fig = px.bar(
        df, x="wasted_qty", y="category", orientation="h",
        color="wasted_qty", color_continuous_scale=["#F3E5D0", COLORS["red"]],
        labels={"wasted_qty": "Wasted qty", "category": ""},
        text="wasted_qty",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, **{k: v for k, v in LAYOUT_BASE.items() if k in ("font", "margin", "paper_bgcolor", "plot_bgcolor")})
    st.plotly_chart(fig, use_container_width=True, key=key)


def weekly_waste_value(series: list[dict], key: str = "weekly_waste") -> None:
    """Estimated wasted value per week."""
    df = pd.DataFrame(series)
    if df.empty:
        return
    fig = px.bar(
        df, x="week", y="wasted_value",
        labels={"wasted_value": "Est. wasted value ($)", "week": "Week"},
        color_discrete_sequence=[COLORS["orange"]],
    )
    _apply_layout(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


def match_pct_bars(recs: list[dict], key: str = "match_bars") -> None:
    """Ingredient match percentage for top recommendations."""
    df = pd.DataFrame([
        {"recipe": r["recipe"][:34], "match_pct": r["match_pct"],
         "score": r["score"]}
        for r in recs[:8]
    ])
    if df.empty:
        return
    df = df.sort_values("match_pct", ascending=True)
    fig = px.bar(
        df, x="match_pct", y="recipe", orientation="h",
        color="match_pct", color_continuous_scale=["#DCE8DD", COLORS["green"]],
        labels={"match_pct": "Ingredient match %", "recipe": ""},
        text="match_pct",
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_layout(coloraxis_showscale=False,
                      paper_bgcolor=COLORS["paper"], plot_bgcolor=COLORS["paper"],
                      font=dict(color=COLORS["ink"], size=12),
                      margin=dict(l=10, r=20, t=10, b=30))
    st.plotly_chart(fig, use_container_width=True, key=key)


def category_inventory_chart(items: list[dict], key: str = "cat_inv") -> None:
    """Active items by category."""
    df = pd.DataFrame(items)
    if df.empty:
        return
    counts = df["category"].value_counts().reset_index()
    counts.columns = ["category", "count"]
    fig = px.bar(
        counts, x="count", y="category", orientation="h",
        color="count", color_continuous_scale=["#DCE8DD", COLORS["green"]],
        labels={"count": "Items", "category": ""}, text="count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
                      paper_bgcolor=COLORS["paper"], plot_bgcolor=COLORS["paper"],
                      font=dict(color=COLORS["ink"], size=12),
                      margin=dict(l=10, r=20, t=10, b=30))
    st.plotly_chart(fig, use_container_width=True, key=key)
