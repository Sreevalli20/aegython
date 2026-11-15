# AI/ML Methodology

## What the "AI" actually is

WasteLess AI uses **classical information retrieval**, not deep learning:

1. **Normalization** — ingredient names are lowercased, stripped of
   punctuation/quantities/descriptors, mapped through a ~140-entry alias table
   (e.g. capsicum→bell pepper, courgette→zucchini, coriander→cilantro), and
   lightly singularized.
2. **TF-IDF vectorization** — each recipe's ingredient list becomes a sparse
   term-frequency × inverse-document-frequency vector over the recipe corpus
   (102 recipes). The pantry inventory becomes a single "query" document.
3. **Cosine similarity** — query vector vs each recipe vector gives a
   semantic-ish relevance score (scikit-learn `TfidfVectorizer` +
   `cosine_similarity`).
4. **Weighted coverage** — ingredient-set overlap weighted by IDF, so matching
   a rare ingredient (e.g. "paneer") counts more than matching "salt".
5. **Expiry-aware boost** — recipes using items expiring within 3 days get up
   to +0.15 score, surfacing "use it before it dies" meals.

Final score: `0.5·cosine + 0.5·IDF-weighted coverage + expiry_boost`,
filtered by minimum coverage and ranked.

**Fallback:** if scikit-learn cannot be imported, an equivalent pure-Python
TF-IDF/cosine implementation runs instead (same math, slower). No external
service is ever contacted.

## What is NOT ML (deterministic business logic)

- Expiry urgency thresholds (0/1/3/7-day bands) — transparent rules with
  written reasoning.
- Shopping duplicate detection — normalized-name matching + quantity checks.
- Restock suggestions — `quantity <= min_threshold`.
- Analytics — SQL aggregations over recorded events.

## Explainability

Every recommendation exposes: match %, matched/missing ingredient lists,
expiring ingredients used, cuisine/prep-time/difficulty, and a natural-language
reason built from those computed fields. Expiry items expose days remaining,
the date type, reasons and a suggested action.

## Evaluation

A labelled eval set (`tests/test_recommendations.py::EVAL_CASES`) measures
Precision@K over 4 scenarios against a 4-recipe fixture, plus a smoke test on
the full bundled dataset. Methodology and recorded results: `docs/TESTING.md`.
