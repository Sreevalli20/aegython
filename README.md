# WasteLess AI

**Know what you have. Know what to use. Waste less.**

An offline-first household food-management and food-waste prevention platform.
WasteLess AI tracks your pantry inventory, expiry dates, shopping list and
consumption history — then uses local machine learning (TF-IDF + cosine
similarity) to recommend meals that use what you already have, prioritizing
ingredients that are about to expire.

https://aegython-cexrpengsxwazjdq6fdjst.streamlit.app/

> Built for **AEGYTHON 2026 — Challenge 06: AI for Everyday Life**.
> Individual team: **Brain Catalyst**.

---

## The problem

Households regularly forget what is in the fridge, lose track of expiry dates,
buy duplicates, and throw away usable food. UK/US studies consistently show
households waste roughly **a third of purchased food by value**. WasteLess AI
attacks this with inventory intelligence, expiry awareness, meal
recommendations and waste analytics — all running **locally, with no external
AI APIs**.

## Who it's for

- Households that want to cut food waste and save money.
- Anyone who has ever found expired food at the back of the fridge.
- Hackathon judges evaluating practical, everyday AI.

## Features

| Module | What it does |
|---|---|
| **Smart Pantry** | Full CRUD inventory: quantity, unit, category, location, purchase & expiry dates, price, low-stock thresholds. Partial consumption, mark used/wasted, consumption history. SQLite persistence. |
| **Expiry Intelligence** | Explainable urgency engine: every item is classified (Expired / Use today / Expiring soon / Plan to use / Fresh / No date) with written reasons and a suggested action. Distinguishes best-before vs use-by dates and defers to labels for safety. |
| **Discover Meals** | Offline recommendation engine over 100+ bundled recipes: ingredient normalization + alias resolution, TF-IDF vectorization, cosine similarity, IDF-weighted coverage, expiry-aware boosting. Every recommendation explains matches, missing ingredients and why it was ranked. |
| **Waste Prevention** | Daily action plan generated only from real records: expiring items to cook/save, top matched meals, restock suggestions, "don't buy again" list, duplicate-purchase checker. |
| **Shopping List** | Add/remove/mark-purchased, auto restock suggestions from low-stock thresholds, live pantry-duplicate warnings, estimated totals. |
| **Analytics** | Recorded consumed/wasted events, estimated wasted value, daily/weekly trends, waste by category, most-wasted ingredients, inventory composition. Estimates clearly labelled. |
| **What-if Simulator** | Hypothetical purchases + consumption/waste assumptions re-scored against real inventory. Outputs explicitly labelled estimates. |
| **Settings** | Local SQLite storage info, sample data loader, full data wipe, privacy notes. |

## Architecture

```
User Inventory
      │
      ▼
Input Validation          (src/validators.py)
      │
      ▼
Ingredient Normalization  (src/recommendation_engine.py — aliases, stemming-lite)
      │
      ▼
Feature Extraction        (TF-IDF vectors, scikit-learn; pure-Python fallback)
      │
      ├──► Expiry Engine   (src/expiry_engine.py — explainable urgency rules)
      └──► Recommendation Engine (cosine similarity + IDF-weighted coverage
                                  + expiry boost → ranked, explained meals)
      │
      ▼
Ranking & Decision Logic  (src/waste_engine.py, src/shopping_engine.py)
      │
      ▼
Explainable Recommendations → Streamlit UI (app.py + views/ + components/)
```

```
wasteless-ai/
├── app.py                  # Streamlit entrypoint + navigation
├── requirements.txt
├── .streamlit/config.toml
├── src/                    # All business logic (no UI code)
│   ├── database.py         # SQLite persistence
│   ├── validators.py       # Input validation
│   ├── inventory.py        # Pantry CRUD + consumption log
│   ├── expiry_engine.py    # Explainable expiry classification
│   ├── recommendation_engine.py  # TF-IDF + cosine-similarity ML
│   ├── waste_engine.py     # Daily prevention plan + risk score
│   ├── shopping_engine.py  # Shopping list + duplicate/restock logic
│   ├── analytics_engine.py # Trends and waste metrics
│   └── simulator.py        # What-if scenarios
├── views/                  # One module per UI page
├── components/             # Reusable UI (cards, badges, charts, CSS)
├── data/
│   ├── sample_inventory.json  # Demo household dataset
│   └── recipes.json           # 100+ curated recipes (CC0)
├── tests/                  # pytest suite (55 tests)
└── docs/                   # Architecture, methodology, attribution, demo script
```

## AI/ML methodology (honest version)

- **What is ML here:** TF-IDF vectorization of recipe ingredient documents and
  the pantry "query" document, cosine similarity ranking, and IDF-weighted
  ingredient coverage. This is classical information retrieval — **not deep
  learning**.
- **What is deterministic logic:** expiry urgency classification, shopping
  duplicate detection, restock thresholds, analytics aggregation.
- **Fallback:** if scikit-learn is unavailable, a pure-Python TF-IDF cosine
  implementation produces equivalent rankings.
- **Explainability:** every recommendation lists matched ingredients, missing
  ingredients, match percentage, expiring ingredients used, and written reasons.

See `docs/AI_ML_METHODOLOGY.md` for the full pipeline and formulas.

## Quick start

```bash
# 1. Install dependencies (Python 3.11+; developed on 3.14)
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Open http://localhost:8501 → click **Load sample data** (Settings or the empty
state) to explore with a demo household.

## Testing

```bash
python -m pytest tests/ -v
```

55 tests covering inventory CRUD, validation, expiry classification edge cases,
recipe matching/missing-ingredient/ranking behavior, a documented
Precision@K evaluation set, shopping duplicates, analytics aggregation and
empty/malformed inputs. See `docs/TESTING.md` for the evaluation methodology
and recorded results.

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io → **New app** → select the repo, branch,
   and `app.py` as the entrypoint.
3. In **Advanced settings**, paste `requirements.txt` as the dependencies file.
4. Deploy. The app stores its SQLite database under `data/` on the container's
   ephemeral filesystem — data resets on redeploy; export/clear options are in
   Settings.

## Data & privacy

- **Offline-first:** no accounts, no external AI APIs, no telemetry.
- All user data lives in a local SQLite file (`data/wasteless.db`, git-ignored).
- Recipes: project-curated dataset, CC0 — see `docs/DATA_ATTRIBUTION.md`.
- Sample inventory: bundled demo data, clearly labelled.

## Food-safety notice

Expiry dates are **labels**, not safety verdicts. WasteLess AI distinguishes
best-before (quality) from use-by (safety-critical) dates and always defers to
package instructions and local food-safety guidance. It never declares food
safe or unsafe.

## Known limitations

See `docs/LIMITATIONS.md` — includes unit-mixing in matching, price estimates,
SQLite ephemerality on Streamlit Cloud, and recipe dataset coverage.

## License

MIT — see `LICENSE`. Recipe dataset content is CC0.
