# Demo Script — ~110 seconds

**Setup before recording:** `streamlit run app.py`, click **Load sample data**
in Settings (or use the empty-state button on Home).

| Time | Screen | Action / narration |
|---|---|---|
| 0–10s | Home Dashboard | "Every year, households throw away about a third of the food they buy. WasteLess AI helps you know what you have, what to use first, and what not to buy again — fully offline, no AI APIs." |
| 10–30s | My Pantry | Show the seeded inventory table. "Every item has quantity, expiry date, storage location and price — stored in a local SQLite database." Open an item: show expiry date + urgency badge. Click **Mark wasted** on the expired banana → "waste is logged, not hidden." |
| 30–50s | Expiry Intelligence | "The expiry engine classifies every item with written reasoning — not a black box." Expand an item: show days remaining, reasons, suggested action. Point at the use-by vs best-before distinction. "It never claims food is safe — it defers to the label." |
| 50–75s | Discover Meals | "Now the ML part: recipes are vectorized with TF-IDF and ranked by cosine similarity against your actual pantry — plus a boost for ingredients expiring within 3 days." Show top recipe card: match %, matched vs missing ingredients, 'uses expiring items' chip, and the written explanation. "This isn't hardcoded — change your pantry and rankings change." |
| 75–90s | Waste Prevention | "A daily plan built only from real records: what to cook, what to save, what not to rebuy." Show duplicate-purchase check: type 'Milk' → "you already have 1L in stock." |
| 90–100s | Analytics | "Every consume/waste action feeds analytics: trends, categories, estimated wasted value — clearly labelled as estimates." |
| 100–110s | Close | "WasteLess AI: offline-first, explainable, privacy-respecting. Streamlit + SQLite + scikit-learn. No external AI services." |

## Recording tips

- Pre-seed sample data so expiry alerts and meal matches are visible immediately.
- Zoom browser to ~110% for readable text.
- Keep sentences short; let the UI carry the detail.
