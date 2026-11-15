"""Discover Meals — recipe recommendations matched to your pantry."""

from __future__ import annotations

import streamlit as st

from components import charts, imagery, ui
from src import inventory, recommendation_engine, shopping_engine


def _ingredient_label(tok: str) -> str:
    return tok.replace("_", " ").title()


def _meal_card_html(i: int, r: dict) -> str:
    exp_chip = ""
    if r["expiring_ingredients"]:
        names = ", ".join(ui.esc(n) for n in r["expiring_ingredients"][:3])
        exp_chip = ui.badge(f"⏳ Uses expiring: {names}", "high")
    meta = " · ".join(x for x in [
        r.get("cuisine"), r.get("meal_type"),
        f"~{r['prep_time_min']} min" if r.get("prep_time_min") else "",
        f"{r['servings']} servings" if r.get("servings") else "",
        r.get("difficulty", ""),
    ] if x)
    have = ", ".join(r["matched"][:8]) or "—"
    missing = ", ".join(r["missing"][:8]) or "nothing — fully stocked!"
    match_color = ("#1E5B3A" if r["match_pct"] >= 70
                   else "#D35400" if r["match_pct"] >= 40 else "#6B7280")
    body = (
        f'<div style="margin-top:8px;font-size:.85rem">'
        f'<span class="wl-chip">🥬 Have: {ui.esc(have)}</span></div>'
        f'<div style="margin-top:6px;font-size:.85rem">'
        f'<span class="wl-chip {"red" if r["missing"] else ""}">'
        f'🛒 Missing: {ui.esc(missing)}</span></div>'
        f'<div style="margin-top:8px;font-size:.82rem;color:#71806F">'
        f'{ui.esc(meta)}</div>'
    )
    extra = (
        f'<div style="text-align:right;flex-shrink:0">'
        f'<div style="font-family:Fraunces,Georgia,serif;font-size:1.35rem;'
        f'font-weight:700;color:{match_color}">{r["match_pct"]:.0f}%</div>'
        f'<div style="font-size:.7rem;color:#71806F">pantry match</div>'
        f'{exp_chip}</div>'
    )
    return imagery.recipe_card(
        {**r, "name": r["recipe"]}, i,
        extra_html=extra, body_html=body)


def render(db_path=None) -> None:
    ui.page_header(
        "Discover Meals",
        "Recipes ranked against what's actually in your kitchen — expiring "
        "ingredients get priority so nothing goes to waste.",
    )

    items = inventory.list_items(db_path=db_path, status="active")
    if not items:
        ui.empty_state("🍽️", "No ingredients to match",
                       "Add items to your pantry first — recommendations are built "
                       "from your real inventory.")
        return

    # Controls
    c1, c2, c3 = st.columns([2, 1, 1])
    top_k = c1.slider("Show top", 3, 15, 8, key="meals_topk")
    max_missing = c2.slider("Max missing ingredients", 1, 8, 5, key="meals_maxmiss")
    meal_filter = c3.selectbox("Meal type", ["Any", "Breakfast", "Lunch", "Dinner", "Snack", "Dessert", "Side"],
                               key="meals_type")

    with st.spinner("Finding meals that match your pantry…"):
        result = recommendation_engine.recommend_meals(items=items, top_k=top_k * 3, db_path=db_path)
    recs = result["recommendations"]
    if meal_filter != "Any":
        recs = [r for r in recs if r.get("meal_type") == meal_filter]
    recs = [r for r in recs if len(r["missing"]) <= max_missing][:top_k]

    stats = result["stats"]
    st.caption(
        f"{stats.get('matched_any', 0)} of {stats['total_recipes']} recipes "
        "matched your pantry."
    )

    if not recs:
        ui.empty_state("🧑‍🍳", "No strong matches",
                       "Try relaxing 'max missing ingredients' or adding more staples to your pantry.")
        return

    charts.match_pct_bars(recs, key="meals_match_bars")

    ui.section_label("Ranked for you")
    for i, r in enumerate(recs, 1):
        ui.raw_html(_meal_card_html(i, r))

        if r["missing"]:
            if st.button(f"Add missing ingredients of '{r['recipe']}' to shopping list",
                         key=f"shop_missing_{i}", width="stretch"):
                added, skipped = 0, 0
                for tok in r["missing"]:
                    name = _ingredient_label(tok)
                    try:
                        shopping_engine.add_item(name, quantity=1, unit="pcs",
                                                  source="recipe_gap", db_path=db_path)
                        added += 1
                    except Exception:
                        skipped += 1
                st.success(f"Added {added} item(s) to your shopping list"
                           + (f" ({skipped} already listed)" if skipped else "") + ".")
                st.rerun()

    ui.note(
        "Match % shows how much of each recipe you already have. Recipes that "
        "use ingredients expiring soon are boosted so you can cook them first.",
        "gold",
    )
