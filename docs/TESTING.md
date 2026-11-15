# Testing & Validation

## Suite

`python -m pytest tests/ -v` — **55 tests, all passing** (run 2026-11-15,
Python 3.14.6, Windows).

| File | Coverage |
|---|---|
| test_inventory.py | add/get/update/delete, invalid qty/dates, partial+full consume, mark wasted/discarded, history, filters, empty DB |
| test_expiry.py | every urgency band, use-by vs best-before, no-date & malformed dates, sort order, summary counts |
| test_validators.py | names, quantities, units, categories, dates, prices, date types, malformed input |
| test_recommendations.py | normalization/aliases, matching, missing ingredients, ranking shifts with inventory, expiry boost, explanations, eval Precision@K, real-dataset smoke test |
| test_shopping.py | CRUD, duplicate rejection, purchase marking, pantry match, restock suggestions, totals |
| test_analytics.py | empty dataset, consumption/waste summaries, top-wasted, category breakdown, daily/weekly series, inventory value |

## Recommendation evaluation methodology

`tests/test_recommendations.py::EVAL_CASES` defines 4 labelled scenarios:
each lists a pantry (e.g. eggs+milk+cheese+spinach) and the recipe expected in
top-3. `test_evaluation_precision_at_k` runs the real engine and computes
Precision@K = retrieved-expected / total-expected.

- Fixture: 4-recipe controlled set (`SAMPLE_RECIPES`) for determinism.
- Additionally `test_real_dataset_loads_and_recommends` smoke-tests the full
  102-recipe bundled dataset against the sample household inventory.

**Recorded result:** Precision@K = 1.00 on the labelled eval set (all 4
expected recipes retrieved in top-3). This is a small sanity-check set, not a
benchmark — it verifies the matcher behaves sensibly, not that it generalizes.

## UI verification

All 9 pages were executed headlessly via `streamlit.testing.v1.AppTest` —
both on an empty database and with the sample dataset loaded — with zero
exceptions.

## What is NOT claimed

- No fabricated metrics: all analytics shown in the UI derive from recorded
  events or are labelled "est." (quantity × unit price).
- No claim of deep learning — the recommender is TF-IDF + cosine similarity.
