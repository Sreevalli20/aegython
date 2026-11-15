"""Food photography for recipe and ingredient cards.

Maps recipes/ingredients to real food photography (Unsplash CDN). Every
image degrades gracefully to an emoji on a forest-green gradient when a
photo is unavailable, so the UI never shows a broken image.
"""

from __future__ import annotations

from . import ui

_BASE = "https://images.unsplash.com/{pid}?w=640&q=80&auto=format&fit=crop"

# Verified live Unsplash photo IDs (checked 2026-11).
PHOTOS = {
    "salad": "photo-1512621776951-a57141f2eefd",
    "bowl": "photo-1546069901-ba9599a7e63c",
    "veggie_bowl": "photo-1540189549336-e6e99c3679fe",
    "pizza": "photo-1565299624946-b28f40a0ae38",
    "pancakes": "photo-1567620905732-2d1ec7ab7445",
    "french_toast": "photo-1484723091739-30a097e8f929",
    "toast": "photo-1482049016688-2d3e1b311543",
    "breakfast": "photo-1493770348161-369560ae357d",
    "eggs": "photo-1551218808-94e220e084d2",
    "dessert": "photo-1565958011703-44f9829ba187",
    "cake": "photo-1551024506-0bccd828d307",
    "sweet": "photo-1533089860892-a7c6f0a88666",
    "icecream": "photo-1563805042-7684c019e1cb",
    "meat": "photo-1504674900247-0877df9cc836",
    "steak": "photo-1432139555190-58524dae6a55",
    "plated": "photo-1414235077428-338989a2e8c0",
    "salmon": "photo-1467003909585-2f8a72700288",
    "soup": "photo-1547592166-23ac45744acd",
    "stew": "photo-1547592180-85f173990554",
    "curry": "photo-1565557623262-b51c2513a641",
    "asian": "photo-1455619452474-d2be8b1e70cd",
    "rice": "photo-1512058564366-18510be2db19",
    "noodles": "photo-1585032226651-759b368d7246",
    "pasta": "photo-1563379091339-03b21ab4a4f8",
    "pasta2": "photo-1473093295043-cdd812d0e601",
    "flatlay": "photo-1490645935967-10de6ba17061",
    "hero": "photo-1476224203421-9ac39bcb3327",
    "bread": "photo-1509440159596-0249088772ff",
    "bakery": "photo-1495521821757-a1efb6729352",
    "kitchen": "photo-1556910103-1c02745aae4d",
    "juice": "photo-1543339308-43e59d6b73a6",
    "coffee": "photo-1504754524776-8f4f37790ca0",
    "smoothie": "photo-1511690656952-34342bb7c2f2",
}

# Ordered keyword -> photo-key rules. First match wins; checked against
# recipe name + ingredient names lowercased.
_RULES = [
    (("pizza",), "pizza"),
    (("pancake", "waffle"), "pancakes"),
    (("french toast", "frenchtoast"), "french_toast"),
    (("toast", "bread", "bagel", "croissant", "bun", "roll", "sandwich",
      "burger", "wrap", "taco", "burrito", "gyro", "panini"), "toast"),
    (("omelette", "omelet", "egg", "scramble", "frittata", "quiche"), "eggs"),
    (("cereal", "oat", "porridge", "granola", "muesli"), "breakfast"),
    (("smoothie", "milkshake", "juice", "beverage", "drink"), "smoothie"),
    (("coffee", "tea", "latte"), "coffee"),
    (("ice cream", "icecream", "gelato", "sorbet", "frozen yogurt"), "icecream"),
    (("cake", "cupcake", "muffin", "brownie", "cookie", "pastry", "pie",
      "tart", "donut", "doughnut", "pudding", "custard", "mousse",
      "cheesecake", "trifle"), "cake"),
    (("chocolate", "cocoa", "fudge"), "sweet"),
    (("dessert", "sweet", "pudding", "kheer", "payasam", "gulab", "jalebi"), "dessert"),
    (("soup", "broth", "chowder", "bisque", "ramen"), "soup"),
    (("stew", "casserole", "hotpot", "tagine", "dal", "khichdi"), "stew"),
    (("curry", "masala", "tikka", "vindaloo", "butter chicken", "korma",
      "rogan", "sambar", "rasam", "thai", "panang", "green curry"), "curry"),
    (("noodle", "ramen", "udon", "soba", "pho", "lo mein", "pad thai",
      "yakisoba"), "noodles"),
    (("pasta", "spaghetti", "penne", "fusilli", "lasagna", "macaroni",
      "mac and cheese", "ravioli", "linguine", "fettuccine", "carbonara",
      "alfredo", "pesto"), "pasta"),
    (("rice", "biryani", "pilaf", "paella", "risotto", "fried rice",
      "jollof", "casserole"), "rice"),
    (("salmon", "trout", "cod", "fish", "tuna", "shrimp", "prawn", "seafood",
      "scallop", "crab"), "salmon"),
    (("steak", "beef", "lamb", "pork", "chicken", "turkey", "meat", "sausage",
      "bacon", "ham", "kebab", "bbq", "barbecue", "roast"), "meat"),
    (("salad", "greek salad", "caesar", "coleslaw"), "salad"),
    (("bowl", "grain bowl", "poke", "acai"), "bowl"),
    (("veggie", "vegetable", "veg ", "tofu", "paneer", "lentil", "chickpea",
      "bean", "falafel", "quinoa", "veg"), "veggie_bowl"),
    (("stir fry", "stir-fry", "stirfry", "wok", "kung pao", "schezwan",
      "schezuan", "asian", "sushi", "dumpling", "teriyaki", "tempura"), "asian"),
    (("currywurst", "wrap"), "asian"),
    (("breakfast", "brunch"), "breakfast"),
    (("flatlay", "platter", "feast"), "flatlay"),
    (("bread", "sourdough", "garlic bread", "naan", "pita", "flatbread",
      "focaccia", "pretzel", "muffin"), "bread"),
    (("pastry", "croissant", "danish", "eclair", "macaron"), "bakery"),
    (("drink", "beverage", "mocktail", "cocktail", "lemonade", "tea",
      "coffee", "smoothie", "shake"), "juice"),
]

_MEAL_PHOTO = {
    "breakfast": "breakfast", "lunch": "bowl", "dinner": "plated",
    "snack": "toast", "dessert": "dessert", "side": "veggie_bowl",
}
_CUISINE_PHOTO = {
    "indian": "curry", "thai": "curry", "chinese": "asian",
    "japanese": "asian", "korean": "asian", "asian": "asian",
    "italian": "pasta", "mediterranean": "salad",
    "american": "meat", "french": "plated",
}


def _photo_url(key: str) -> str:
    return _BASE.format(pid=PHOTOS[key])


def recipe_photo_key(recipe: dict) -> str:
    """Pick the best photo key for a recipe dict (name, ingredients, tags…)."""
    parts = [str(recipe.get("name", ""))]
    for ing in recipe.get("ingredients", []) or []:
        parts.append(ing.get("name", "") if isinstance(ing, dict) else str(ing))
    parts.extend(recipe.get("tags") or [])
    text = " " + " ".join(parts).lower() + " "
    for keywords, key in _RULES:
        if any(k in text for k in keywords):
            return key
    meal = str(recipe.get("meal_type", "")).lower()
    if meal in _MEAL_PHOTO:
        return _MEAL_PHOTO[meal]
    cuisine = str(recipe.get("cuisine", "")).lower()
    for c, key in _CUISINE_PHOTO.items():
        if c in cuisine:
            return key
    return "hero"


def recipe_photo(recipe: dict) -> str:
    return _photo_url(recipe_photo_key(recipe))


def recipe_emoji(recipe: dict) -> str:
    key = recipe_photo_key(recipe)
    return {
        "pizza": "🍕", "pancakes": "🥞", "french_toast": "🍞",
        "toast": "🥪", "eggs": "🍳", "breakfast": "🍳", "smoothie": "🥤",
        "coffee": "☕", "icecream": "🍦", "cake": "🍰", "sweet": "🍫",
        "dessert": "🍮", "soup": "🍲", "stew": "🍲", "curry": "🍛",
        "noodles": "🍜", "pasta": "🍝", "rice": "🍚", "salmon": "🐟",
        "meat": "🥩", "salad": "🥗", "bowl": "🥙", "veggie_bowl": "🥦",
        "asian": "🍱", "flatlay": "🍽️", "bread": "🍞", "bakery": "🥐",
        "juice": "🧃", "hero": "🍽️", "plated": "🍽️",
    }.get(key, "🍽️")


def recipe_card(recipe: dict, rank: int, extra_html: str = "",
                body_html: str = "") -> str:
    """A premium recipe card: photo strip + content body."""
    url = recipe_photo(recipe)
    emoji = recipe_emoji(recipe)
    name = ui.esc(recipe.get("name", "Recipe"))
    photo = ui.photo_block(url, emoji=emoji, caption="", height=170)
    return (
        f'<div class="wl-card wl-recipe-card" style="padding:0">'
        f'<div class="wl-recipe-photo">{photo}</div>'
        f'<div class="wl-recipe-body">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">'
        f'<div><span class="wl-badge gold" style="margin-bottom:6px;display:inline-block">'
        f'#{rank}</span><br/><b style="font-size:1.08rem;font-family:Fraunces,Georgia,serif">'
        f'{name}</b></div>{extra_html}</div>'
        f'{body_html}</div></div>'
    )


def ingredient_photo(name: str) -> str | None:
    """Best-effort photo for a pantry/shopping ingredient name."""
    text = " " + name.lower() + " "
    for keywords, key in _RULES:
        if any(k in text for k in keywords):
            return _photo_url(key)
    return None
