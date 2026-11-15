# Known Limitations

1. **Matching granularity** — ingredient normalization is rule-based
   (aliases + light singularization). Unusual names or compound dishes may
   match imperfectly; e.g. "chicken breast" maps to "chicken", which can blur
   distinct cuts.
2. **Units are not converted** — "500 g chicken" and a recipe needing "2
   chicken breasts" match by name only; quantities are not reconciled across
   units.
3. **Price estimates** — waste "value" uses purchase price ÷ quantity at event
   time. It is an approximation, not audited savings.
4. **Expiry ≠ safety** — the engine surfaces label dates and never judges
   whether food is safe. Use-by items always defer to the package label.
5. **Single household** — the SQLite DB assumes one household; no multi-user,
   sync or backup features.
6. **Streamlit Cloud persistence** — the free tier filesystem is ephemeral;
   the database resets on redeploy/sleep. Treat it as a demo environment.
7. **Recipe coverage** — 102 curated recipes cover common dishes but not every
   cuisine; missing-ingredient suggestions are generic names ("bell pepper"),
   not package sizes.
8. **No image/receipt/barcode input** — inventory is entered manually.
9. **Simulator is directional** — it re-scores inventory under assumptions;
   it does not model real consumption dynamics.
10. **Language** — English ingredient names only.
