"""Discover Meals — TF-IDF + cosine-similarity recipe recommendations."""

from __future__ import annotations

import streamlit as st

from components import charts, ui
from src import inventory, recommendation_engine, shopping_engine
from src.recommendation_engine import normalize_ingredient


def _ingredient_label(tok: str) -> str:
    return tok.replace("_", " ").title()


def render(db_path=None) -> None:
    ui.page_header(
        "Discover Meals",
        "Recipes ranked against YOUR pantry using TF-IDF vectorization and cosine similarity "
        "(offline, scikit-learn). Expiring ingredients boost recipes that use them.",
    )

    items = inventory.list_items(db_path=db_path, status="active")
    if not items:
        ui.empty_state("🍽️", "No ingredients to match",
                       "Add items to your pantry first — recommendations are computed "
                       "from your real inventory.")
        return

    # Controls
    c1, c2, c3 = st.columns([2, 1, 1])
    top_k = c1.slider("Show top", 3, 15, 8, key="meals_topk")
    max_missing = c2.slider("Max missing ingredients", 1, 8, 5, key="meals_maxmiss")
    meal_filter = c3.selectbox("Meal type", ["Any", "Breakfast", "Lunch", "Dinner", "Snack", "Dessert", "Side"],
                               key="meals_type")

    with st.spinner("Computing recommendations from your pantry…"):
        result = recommendation_engine.recommend_meals(items=items, top_k=top_k * 3, db_path=db_path)
    recs = result["recommendations"]
    if meal_filter != "Any":
        recs = [r for r in recs if r.get("meal_type") == meal_filter]
    # cap by missing count
    recs = [r for r in recs if len(r["missing"]) <= max_missing][:top_k]

    stats = result["stats"]
    st.caption(
        f"Engine: **{stats['engine']}** · {stats['total_recipes']} recipes indexed · "
        f"{stats.get('matched_any', 0)} recipes matched your inventory."
    )

    if not recs:
        ui.empty_state("🧑‍🍳", "No strong matches",
                       "Try relaxing 'max missing ingredients' or adding more staples to your pantry.")
        return

    charts.match_pct_bars(recs, key="meals_match_bars")

    ui.section_label("Ranked recommendations")
    for i, r in enumerate(recs, 1):
        exp_chip = ""
        if r["expiring_ingredients"]:
            exp_names = ", ".join(ui.esc(n) for n in r["expiring_ingredients"][:3])
            exp_chip = ('<span class="wl-badge high" style="margin-left:8px">'
                        f'⏳ uses expiring: {exp_names}</span>')
        meta = " · ".join(x for x in [
            r.get("cuisine"), r.get("meal_type"),
            f"~{r['prep_time_min']} min" if r.get("prep_time_min") else "",
            f"{r['servings']} servings" if r.get("servings") else "",
            r.get("difficulty", ""),
        ] if x)
        have = ", ".join(r["matched"][:8]) or "—"
        missing = ", ".join(r["missing"][:8]) or "nothing — fully stocked!"
        reasons = " ".join(r["reasons"])
        match_color = ("#1B7A43" if r["match_pct"] >= 70
                       else "#D35400" if r["match_pct"] >= 40 else "#6B7280")
        ui.raw_html(
            f'<div class="wl-card"><div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;gap:12px">'
            f'<div><b style="font-size:1.05rem">{i}. {ui.esc(r["recipe"])}</b>{exp_chip}<br/>'
            f'<span style="color:#6B7280;font-size:.82rem">{ui.esc(meta)}</span></div>'
            f'<div style="text-align:right"><div style="font-size:1.4rem;font-weight:800;'
            f'color:{match_color}">'
            f'{r["match_pct"]:.0f}%</div><div style="font-size:.72rem;color:#6B7280">match</div></div>'
            f'</div>'
            f'<div style="margin-top:8px;font-size:.85rem">'
            f'<b>Have:</b> {ui.esc(have)}'
            f' &nbsp;·&nbsp; <b>Missing:</b> '
            f'<span style="color:{"#B3261E" if r["missing"] else "#1B7A43"}">'
            f'{ui.esc(missing)}</span></div>'
            f'<div style="margin-top:6px;font-size:.83rem;color:#33413a">'
            f'💡 {ui.esc(reasons)}</div></div>'
        )

        if r["missing"]:
            if st.button(f"Add missing ingredients of '{r['recipe']}' to shopping list",
                         key=f"shop_missing_{i}", width="stretch"):
                added, skipped = 0, 0
                for tok in r["missing"]:
                    # display name: title-cased token (canonical form)
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
        "**How it works:** each pantry item and recipe ingredient is normalized "
        "(lowercase, punctuation stripped, aliases like 'capsicum'→'bell pepper' resolved), "
        "then vectorized with TF-IDF. Recipes are ranked by cosine similarity blended with "
        "IDF-weighted ingredient coverage, plus a boost for recipes using items expiring "
        "within 3 days. Match % = share of recipe ingredients you already have.",
        "info",
    )
