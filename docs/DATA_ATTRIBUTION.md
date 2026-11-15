# Data Attribution & Licensing

## Recipe dataset (`data/recipes.json`)

- **Source:** compiled by the WasteLess AI project authors.
- **Content:** 102 common home-cooking recipes (breakfast/lunch/dinner/snack/
  dessert) with ingredients, prep time, servings, cuisine, meal type and
  difficulty.
- **License:** CC0-1.0 (project-authored; public domain dedication).
- **Note:** recipes describe widely known dishes; ingredient lists were written
  for this project and are not copied from any third-party dataset or API.
  No external dataset (RecipeNLG, Recipe1M+, etc.) is used or required.

## Sample inventory (`data/sample_inventory.json`)

- **Source:** authored for this project as demo data.
- **License:** CC0-1.0.
- Dates use `offset:N` = N days relative to load time, so the demo always has
  fresh/expiring/expired examples.

## Libraries

- scikit-learn, scipy, numpy, pandas, plotly, streamlit — all permissive
  open-source licenses (BSD/Apache/MIT). See `requirements.txt`.

## User data

- Created at runtime in `data/wasteless.db` (git-ignored). Never leaves the
  device. Cleared via Settings → "Clear ALL local data".
