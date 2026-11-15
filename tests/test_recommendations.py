"""Recommendation engine tests, including a small documented evaluation set."""

import pytest

from src import inventory, recommendation_engine as rec
from src.recommendation_engine import normalize_ingredient

SAMPLE_RECIPES = [
    {"name": "Veggie Omelette", "ingredients": ["eggs", "milk", "cheese", "spinach"],
     "prep_time_min": 10, "servings": 1, "cuisine": "Test", "meal_type": "Breakfast"},
    {"name": "Tomato Pasta", "ingredients": ["pasta", "tomatoes", "garlic", "olive oil"],
     "prep_time_min": 20, "servings": 4, "cuisine": "Test", "meal_type": "Dinner"},
    {"name": "Beef Curry", "ingredients": ["beef", "curry powder", "onion", "rice"],
     "prep_time_min": 40, "servings": 4, "cuisine": "Test", "meal_type": "Dinner"},
    {"name": "Fruit Parfait", "ingredients": ["yogurt", "banana", "honey", "oats"],
     "prep_time_min": 5, "servings": 1, "cuisine": "Test", "meal_type": "Breakfast"},
]


def _item(name, **kw):
    base = {"id": 1, "name": name, "category": "Other", "quantity": 1,
            "unit": "pcs", "location": "Pantry", "status": "active",
            "purchase_date": "2026-01-01", "expiry_date": None,
            "date_type": "user"}
    base.update(kw)
    return base


def test_normalize_basic():
    assert normalize_ingredient("Chicken Breast") == "chicken"
    assert normalize_ingredient("Fresh Garlic Cloves") == "garlic"
    assert normalize_ingredient("Capsicum (red)") == "bell pepper"
    assert normalize_ingredient("  Eggs!!! ") == "egg"
    assert normalize_ingredient("") == ""


def test_normalize_alias_and_plural():
    assert normalize_ingredient("Coriander") == "cilantro"
    assert normalize_ingredient("Zucchini") == "zucchini"
    assert normalize_ingredient("Courgette") == "zucchini"


def test_engine_matches_inventory():
    items = [_item("Eggs"), _item("Milk"), _item("Cheese"), _item("Spinach"),
             _item("Beef"), _item("Curry Powder"), _item("Onion"), _item("Rice")]
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out = engine.recommend(items=items)
    names = [r["recipe"] for r in out["recommendations"]]
    # Omelette and Beef Curry should both appear; omelette has full coverage.
    assert "Veggie Omelette" in names
    assert "Beef Curry" in names
    omelette = next(r for r in out["recommendations"] if r["recipe"] == "Veggie Omelette")
    assert omelette["match_pct"] == 100.0
    assert omelette["missing"] == []


def test_missing_ingredients_reported():
    items = [_item("Eggs"), _item("Spinach")]
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out = engine.recommend(items=items)
    omelette = next(r for r in out["recommendations"] if r["recipe"] == "Veggie Omelette")
    assert set(omelette["missing"]) == {"milk", "cheese"}
    assert omelette["match_pct"] == pytest.approx(50.0)


def test_ranking_changes_with_inventory():
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out_a = engine.recommend(items=[_item("Eggs"), _item("Milk"), _item("Cheese"), _item("Spinach")])
    out_b = engine.recommend(items=[_item("Pasta"), _item("Tomatoes"), _item("Garlic"), _item("Olive Oil")])
    assert out_a["recommendations"][0]["recipe"] == "Veggie Omelette"
    assert out_b["recommendations"][0]["recipe"] == "Tomato Pasta"


def test_empty_inventory_returns_empty():
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out = engine.recommend(items=[])
    assert out["recommendations"] == []


def test_expiring_ingredient_boost():
    from datetime import date, timedelta
    soon = (date.today() + timedelta(days=1)).isoformat()
    items = [_item("Eggs"), _item("Spinach", id=2, expiry_date=soon)]
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out = engine.recommend(items=items)
    omelette = next(r for r in out["recommendations"] if r["recipe"] == "Veggie Omelette")
    assert omelette["expiring_ingredients"]
    assert any("expiring" in r.lower() for r in omelette["reasons"])


def test_every_rec_has_explanations():
    items = [_item("Eggs"), _item("Milk"), _item("Rice")]
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    out = engine.recommend(items=items)
    for r in out["recommendations"]:
        assert r["reasons"], f"{r['recipe']} missing explanation"
        assert 0 <= r["match_pct"] <= 100
        assert r["score"] > 0


# ---------------------------------------------------------------------------
# Documented evaluation: precision@K over a labelled test set.
# Methodology: each case lists inventory names and the set of recipe names that
# SHOULD appear in the top-K. We measure whether expected recipes are retrieved.
# ---------------------------------------------------------------------------

EVAL_CASES = [
    {
        "inventory": ["eggs", "milk", "cheese", "spinach"],
        "expected_top3": {"Veggie Omelette"},
        "k": 3,
    },
    {
        "inventory": ["pasta", "tomatoes", "garlic", "olive oil"],
        "expected_top3": {"Tomato Pasta"},
        "k": 3,
    },
    {
        "inventory": ["yogurt", "banana", "honey", "oats"],
        "expected_top3": {"Fruit Parfait"},
        "k": 3,
    },
    {
        "inventory": ["beef", "onion", "rice"],  # partial curry ingredients
        "expected_top3": {"Beef Curry"},
        "k": 3,
    },
]


def test_evaluation_precision_at_k():
    """Precision@K on the labelled eval set (documented in docs/TESTING.md)."""
    engine = rec.RecommendationEngine(recipes=SAMPLE_RECIPES)
    hits = 0
    total = 0
    for case in EVAL_CASES:
        items = [_item(n, id=i + 1) for i, n in enumerate(case["inventory"])]
        out = engine.recommend(items=items, top_k=case["k"])
        got = {r["recipe"] for r in out["recommendations"][: case["k"]]}
        expected = case["expected_top3"]
        # Precision contribution: fraction of expected items retrieved.
        retrieved = len(got & expected)
        hits += retrieved
        total += len(expected)
    precision = hits / total if total else 0.0
    # With a tiny curated set we expect strong retrieval; assert a sane floor.
    assert precision >= 0.75, f"Precision@K too low: {precision}"
    print(f"\nEval Precision@K = {precision:.2f} over {len(EVAL_CASES)} cases")


def test_real_dataset_loads_and_recommends(db):
    """Smoke test against the bundled 100+ recipe dataset."""
    n = inventory.add_sample_data(db_path=db)
    assert n > 0
    items = inventory.list_items(db_path=db)
    out = rec.recommend_meals(items=items, top_k=5, db_path=db)
    assert out["stats"]["total_recipes"] >= 90
    assert len(out["recommendations"]) > 0
    top = out["recommendations"][0]
    assert top["match_pct"] > 0
    assert top["reasons"]
