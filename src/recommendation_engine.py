"""Offline meal recommendation engine.

Pipeline:
  inventory items -> ingredient normalization -> TF-IDF vectorization ->
  cosine similarity + weighted ingredient coverage -> expiry-aware ranking ->
  explainable recommendations.

Honesty note: this is classical information retrieval (TF-IDF + cosine
similarity), not deep learning. Everything runs locally; sklearn is used when
available with a pure-Python fallback so the feature never depends on an
external service.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from . import database, expiry_engine, inventory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"

try:  # pragma: no cover - exercised indirectly
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_OK = True
except Exception:  # pragma: no cover
    _SKLEARN_OK = False

# Common household synonyms so "cilantro" matches a recipe asking for
# "coriander", etc. Keys and values are normalized forms.
ALIAS_MAP = {
    "coriander": "cilantro", "cilantro": "cilantro",
    "capsicum": "bell pepper", "bell pepper": "bell pepper", "pepper": "bell pepper",
    "aubergine": "eggplant", "eggplant": "eggplant",
    "zucchini": "zucchini", "courgette": "zucchini",
    "scallion": "spring onion", "spring onions": "spring onion",
    "garlic cloves": "garlic", "garlic clove": "garlic",
    "onion": "onion", "red onion": "onion", "yellow onion": "onion",
    "potato": "potato", "potatoes": "potato",
    "tomato": "tomato", "tomatoes": "tomato",
    "chicken breast": "chicken", "chicken thighs": "chicken", "chicken": "chicken",
    "minced chicken": "chicken", "ground chicken": "chicken",
    "beef mince": "beef", "ground beef": "beef", "beef": "beef",
    "pork": "pork", "bacon": "bacon", "ham": "ham",
    "salmon": "salmon", "tuna": "tuna", "fish": "fish", "prawn": "shrimp", "prawns": "shrimp", "shrimp": "shrimp",
    "egg": "egg", "eggs": "egg",
    "milk": "milk", "butter": "butter", "cheese": "cheese", "cheddar": "cheese",
    "yogurt": "yogurt", "curd": "yogurt",
    "cream": "cream", "heavy cream": "cream",
    "flour": "flour", "all purpose flour": "flour", "plain flour": "flour",
    "rice": "rice", "basmati rice": "rice", "jasmine rice": "rice",
    "pasta": "pasta", "spaghetti": "pasta", "penne": "pasta", "noodles": "noodles", "ramen": "noodles",
    "bread": "bread", "toast": "bread",
    "olive oil": "olive oil", "oil": "oil", "vegetable oil": "oil", "cooking oil": "oil",
    "salt": "salt", "black pepper": "black pepper", "peppercorns": "black pepper",
    "sugar": "sugar", "honey": "honey",
    "soy sauce": "soy sauce", "sesame oil": "sesame oil",
    "lemon": "lemon", "lime": "lime", "lemon juice": "lemon", "lime juice": "lime",
    "carrot": "carrot", "carrots": "carrot",
    "spinach": "spinach", "lettuce": "lettuce", "greens": "spinach", "kale": "spinach",
    "broccoli": "broccoli", "cauliflower": "cauliflower",
    "mushroom": "mushroom", "mushrooms": "mushroom",
    "beans": "beans", "kidney beans": "beans", "black beans": "beans", "chickpeas": "chickpeas", "chickpea": "chickpeas",
    "lentils": "lentils", "lentil": "lentils",
    "coconut milk": "coconut milk", "coconut": "coconut",
    "oats": "oats", "oatmeal": "oats",
    "banana": "banana", "bananas": "banana", "apple": "apple", "apples": "apple",
    "avocado": "avocado", "avocados": "avocado",
    "herbs": "herbs", "parsley": "herbs", "coriander leaves": "herbs", "cilantro leaves": "herbs",
    "chili": "chili", "chilli": "chili", "red chili": "chili", "green chili": "chili",
    "ginger": "ginger", "garlic": "garlic",
    "curry powder": "curry powder", "turmeric": "turmeric", "cumin": "cumin", "coriander powder": "coriander powder",
    "paprika": "paprika", "cumin powder": "cumin",
    "vinegar": "vinegar", "apple cider vinegar": "vinegar",
    "ketchup": "ketchup", "mustard": "mustard", "mayonnaise": "mayonnaise",
    "cereal": "cereal", "cornflakes": "cereal", "granola": "cereal",
    "jam": "jam", "peanut butter": "peanut butter",
    "tofu": "tofu", "paneer": "paneer", "cheddar cheese": "cheese",
    "mozzarella": "cheese", "parmesan": "cheese", "feta": "cheese",
    "cream cheese": "cream cheese", "sour cream": "sour cream",
    "vanilla": "vanilla", "cinnamon": "cinnamon", "cocoa": "cocoa", "chocolate": "chocolate",
    "ice cream": "ice cream", "frozen peas": "peas", "peas": "peas",
    "corn": "corn", "sweet corn": "corn",
    "zucchini": "zucchini", "bell peppers": "bell pepper",
    "raisins": "raisins", "dates": "dates", "nuts": "nuts", "almonds": "nuts", "walnuts": "nuts",
    "oats flour": "flour",
}

_PLURALS = {
    "potatoes": "potato", "tomatoes": "tomato", "carrots": "carrot",
    "mushrooms": "mushroom", "eggs": "egg", "beans": "beans",
    "peas": "peas", "spinach": "spinach", "greens": "spinach",
    "noodles": "noodles", "oats": "oats", "lentils": "lentils",
    "chickpeas": "chickpeas", "biscuits": "biscuit", "cookies": "biscuit",
    "biscuits": "biscuit",
}

_WORD_RE = re.compile(r"[a-z]+")


def normalize_ingredient(name: str) -> str:
    """Canonicalize an ingredient name for matching.

    Lowercases, removes punctuation/quantities, applies the alias map and a
    light singularization pass. Returns the canonical form used for set
    membership tests.
    """
    text = (name or "").lower()
    text = re.sub(r"\(.*?\)", " ", text)          # drop parenthetical notes
    text = re.sub(r"\b\d+(\.\d+)?\s*(g|kg|ml|l|cup|cups|tbsp|tsp|oz|lb|clove|cloves)?\b", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    words = _WORD_RE.findall(text)
    # Drop generic descriptors that don't identify the ingredient.
    stop = {"fresh", "diced", "chopped", "sliced", "minced", "crushed", "large",
            "small", "medium", "ripe", "raw", "cooked", "boiled", "fried",
            "organic", "free", "range", "of", "the", "a", "an", "and", "or",
            "with", "to", "taste", "optional", "for", "serving", "servings"}
    kept = [w for w in words if w not in stop]
    if not kept:
        return ""
    phrase = " ".join(kept)
    # Prefer alias on the full phrase first, then individual tokens.
    if phrase in ALIAS_MAP:
        return ALIAS_MAP[phrase]
    mapped = []
    for w in kept:
        mapped.append(_PLURALS.get(w, w))
    phrase2 = " ".join(mapped)
    if phrase2 in ALIAS_MAP:
        return ALIAS_MAP[phrase2]
    # Collapse multi-word canonical aliases token-wise.
    out = []
    i = 0
    toks = phrase2.split()
    while i < len(toks):
        two = " ".join(toks[i:i + 2])
        if two in ALIAS_MAP:
            out.append(ALIAS_MAP[two])
            i += 2
            continue
        out.append(ALIAS_MAP.get(toks[i], toks[i]))
        i += 1
    canon = " ".join(dict.fromkeys(out))
    return canon.strip()


def load_recipes(path: Path | None = None) -> list[dict]:
    p = path or RECIPES_PATH
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["recipes"] if isinstance(data, dict) else data


def _recipe_tokens(recipe: dict) -> set[str]:
    toks: set[str] = set()
    for ing in recipe.get("ingredients", []):
        if isinstance(ing, dict):
            name = ing.get("name", "")
        else:
            name = str(ing)
        n = normalize_ingredient(name)
        if n:
            toks.add(n)
    return toks


def _inventory_tokens(items: list[dict]) -> dict[str, list[dict]]:
    """Map canonical ingredient token -> list of contributing inventory items."""
    mapping: dict[str, list[dict]] = {}
    for item in items:
        canon = normalize_ingredient(item.get("name", ""))
        if canon:
            mapping.setdefault(canon, []).append(item)
    return mapping


def _expiring_soon_ids(items: list[dict], days: int = 3) -> set[int]:
    ids = set()
    for item in items:
        d = expiry_engine.days_remaining(item.get("expiry_date"))
        if d is not None and d <= days:
            ids.add(item["id"])
    return ids


class RecommendationEngine:
    """Ranks recipes against the current inventory."""

    def __init__(self, recipes: list[dict] | None = None, db_path=None):
        self.recipes = recipes if recipes is not None else load_recipes()
        self.db_path = db_path
        self._prep()

    def _prep(self) -> None:
        for r in self.recipes:
            r["_tokens"] = _recipe_tokens(r)
            r["_doc"] = " ".join(
                normalize_ingredient(i.get("name", "") if isinstance(i, dict) else str(i))
                for i in r.get("ingredients", [])
            )
        self._docs = [r["_doc"] for r in self.recipes]
        # IDF over recipe corpus so rare ingredients weigh more.
        df = Counter()
        for toks in (r["_tokens"] for r in self.recipes):
            df.update(toks)
        n = max(len(self.recipes), 1)
        self._idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}

        self._vectorizer = None
        if _SKLEARN_OK and self._docs:
            try:
                self._vectorizer = TfidfVectorizer(
                    tokenizer=lambda s: s.split(), preprocessor=lambda s: s,
                    token_pattern=None, lowercase=False,
                )
                self._recipe_matrix = self._vectorizer.fit_transform(self._docs)
            except Exception:
                self._vectorizer = None
                self._recipe_matrix = None
        else:
            self._recipe_matrix = None

    def _tfidf_scores(self, query_doc: str) -> list[float]:
        """Cosine similarity between the inventory query and every recipe."""
        if self._vectorizer is not None and self._recipe_matrix is not None:
            try:
                q = self._vectorizer.transform([query_doc])
                sims = cosine_similarity(q, self._recipe_matrix)[0]
                return [float(s) for s in sims]
            except Exception:
                pass
        # Pure-Python TF-IDF cosine fallback.
        docs = self._docs + [query_doc]
        vocab = sorted({t for d in docs for t in d.split()})
        idx = {t: i for i, t in enumerate(vocab)}
        n = len(docs)
        df = Counter()
        for d in docs:
            df.update(set(d.split()))
        idf = {t: math.log((1 + n) / (1 + df[t])) + 1 for t in vocab}

        def vec(d):
            tf = Counter(d.split())
            v = [0.0] * len(vocab)
            for t, c in tf.items():
                v[idx[t]] = (1 + math.log(c)) * idf[t]
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            return [x / norm for x in v]

        qv = vec(query_doc)
        out = []
        for d in self._docs:
            dv = vec(d)
            out.append(sum(a * b for a, b in zip(qv, dv)))
        return out

    def recommend(self, items: list[dict] | None = None, top_k: int = 10,
                  min_match: float = 0.15, db_path=None) -> dict:
        """Rank recipes against inventory.

        Returns {"recommendations": [...], "stats": {...}} where each rec has
        matched/missing ingredients, match percentage, expiring-ingredient
        flags and a written explanation.
        """
        if items is None:
            items = inventory.list_items(db_path=db_path or self.db_path, status="active")
        active = [i for i in items if i.get("status", "active") == "active"]
        inv_map = _inventory_tokens(active)
        inv_tokens = set(inv_map)
        if not inv_tokens:
            return {"recommendations": [], "stats": {"total_recipes": len(self.recipes),
                                                     "matched_any": 0}}

        query_doc = " ".join(
            normalize_ingredient(i.get("name", "")) for i in active
        )
        sims = self._tfidf_scores(query_doc)
        expiring_ids = _expiring_soon_ids(active, days=3)

        results = []
        for recipe, sim in zip(self.recipes, sims):
            toks = recipe["_tokens"]
            if not toks:
                continue
            matched = sorted(toks & inv_tokens)
            missing = sorted(toks - inv_tokens)
            coverage = len(matched) / len(toks)

            # IDF-weighted coverage: matching a rare ingredient counts more.
            w_total = sum(self._idf.get(t, 1.0) for t in toks)
            w_hit = sum(self._idf.get(t, 1.0) for t in matched)
            weighted_cov = w_hit / w_total if w_total else 0.0

            # Expiry-aware boost: recipes that use soon-to-expire items rank higher.
            exp_used = []
            for tok in matched:
                for it in inv_map.get(tok, []):
                    if it.get("id") in expiring_ids:
                        exp_used.append(it["name"])
            exp_used = sorted(set(exp_used))
            expiry_boost = min(0.15, 0.05 * len(exp_used)) if exp_used else 0.0

            score = 0.5 * sim + 0.5 * weighted_cov + expiry_boost
            match_pct = coverage * 100
            if coverage < min_match:
                continue

            reasons = []
            if matched:
                reasons.append(
                    f"Uses {len(matched)}/{len(toks)} of its ingredients from your pantry "
                    f"({', '.join(matched[:4])}{'…' if len(matched) > 4 else ''})."
                )
            if missing:
                reasons.append(
                    f"Missing {len(missing)} ingredient(s): {', '.join(missing[:4])}"
                    f"{'…' if len(missing) > 4 else ''}."
                )
            if exp_used:
                reasons.append(
                    f"Prioritized because it uses items expiring within 3 days: {', '.join(exp_used)}."
                )
            else:
                reasons.append("Good ingredient coverage with items you already have.")

            results.append({
                "recipe": recipe.get("name", "Unnamed recipe"),
                "cuisine": recipe.get("cuisine", ""),
                "meal_type": recipe.get("meal_type", ""),
                "prep_time_min": recipe.get("prep_time_min"),
                "servings": recipe.get("servings"),
                "difficulty": recipe.get("difficulty", ""),
                "score": round(score, 4),
                "tfidf_similarity": round(float(sim), 4),
                "coverage": round(coverage, 4),
                "weighted_coverage": round(weighted_cov, 4),
                "match_pct": round(match_pct, 1),
                "matched": matched,
                "missing": missing,
                "expiring_ingredients": exp_used,
                "reasons": reasons,
                "ingredients": recipe.get("ingredients", []),
            })

        results.sort(key=lambda r: (-r["score"], r["recipe"]))
        top = results[:top_k]
        return {
            "recommendations": top,
            "stats": {
                "total_recipes": len(self.recipes),
                "candidates": len(results),
                "matched_any": len(results),
                "engine": "sklearn-tfidf" if self._vectorizer is not None else "pure-python-tfidf",
            },
        }


_ENGINE: RecommendationEngine | None = None


def get_engine(db_path=None) -> RecommendationEngine:
    global _ENGINE
    if _ENGINE is None or db_path is not None:
        _ENGINE = RecommendationEngine(db_path=db_path)
    return _ENGINE


def recommend_meals(items=None, top_k: int = 10, db_path=None) -> dict:
    return get_engine(db_path).recommend(items=items, top_k=top_k, db_path=db_path)
