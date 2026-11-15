# Architecture

## Layers

```
┌─────────────────────────────────────────────────┐
│  UI layer     app.py, pages/*.py, components/   │  Streamlit
├─────────────────────────────────────────────────┤
│  Engines      expiry, recommendation, waste,    │  Pure Python + sklearn
│               shopping, analytics, simulator    │
├─────────────────────────────────────────────────┤
│  Domain       inventory.py, validators.py       │  CRUD + validation
├─────────────────────────────────────────────────┤
│  Persistence  database.py (SQLite)              │  data/wasteless.db
└─────────────────────────────────────────────────┘
```

Dependency rule: engines never import Streamlit; pages never touch SQL
directly — everything goes through `src/` functions that accept a `db_path`
for testability.

## Data model (SQLite)

- **items** — id, name, category, quantity, unit, purchase_date,
  expiry_date, date_type (`best_before`/`use_by`/`user`), location, price,
  min_threshold, status (`active`/`consumed`/`wasted`/`discarded`), notes,
  timestamps.
- **consumption_log** — item snapshot (name/category), quantity, unit, event,
  event_date, est_value, reason. Append-only history powering analytics.
- **shopping_list** — name, quantity, unit, purchased flag, added_date,
  price_estimate, source (`manual`/`restock`/`recipe_gap`). UNIQUE(name, unit)
  prevents duplicates.

## Key flows

- **Expiry:** `expiry_engine.assess_inventory()` → `classify_item()` per item →
  urgency + reasons + action → sorted by `URGENCY_ORDER`.
- **Meals:** inventory → `normalize_ingredient()` → query document →
  `RecommendationEngine._tfidf_scores()` → per-recipe coverage/missing/IDF
  weighting → expiry boost → ranked list with explanations.
- **Waste plan:** `waste_engine.build_daily_plan()` composes expiry items,
  top meals and restock suggestions into one actionable list.
- **Analytics:** all figures derive from `consumption_log` via
  `analytics_engine`; values are `est_value` recorded at event time.

## Why SQLite

Zero-config, file-based, survives restarts, trivially testable via `db_path`,
and adequate for single-household scale. No server required — matches the
offline-first privacy goal.
