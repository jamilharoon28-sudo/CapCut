# Smart Preflight — Evidence (pack doc 19)

Coach inspects the sources first and tells the owner what it needs, so a beginner
never has to guess. Additive: it runs *before* rendering and never fabricates.

## Built
- `preflight/schemas.py` — typed `PreflightRequirement`, `EvidenceMatch`,
  `RequestCard`, `ReadinessReport` (+ `ReadinessStatus`). Matches doc 19 §6.
- `preflight/engine.py` — deterministic `run_preflight`: builds requirements from
  the script beats + footage/asset/audio/delivery defaults, matches each beat to
  usable footage, then produces **Ready / Ready-with-suggestions / Needs-help**.
  Blocks only for material problems (no usable footage); everything with a safe
  honest fallback (missing logo → text end-card, missing music → clean/silent,
  fewer clips than beats → reuse + a recording request) is a *suggestion*. Every
  card states what's needed, why, the recommended action, a fallback, and the
  quality impact; missing-footage cards include plain recording directions.
- API `POST /projects/{id}/preflight` — inspects the folder/zip, runs light visual
  analysis for quality signals, returns the readiness report + headline.
- UI — a **"Check what I need"** button on the Create screen renders the readiness
  panel with colour-coded request cards before "Create my videos".

## Verified (this CI run)
```
tests/test_preflight.py — 6 passed:
  • no footage → NEEDS_HELP + a recording direction
  • enough footage + story + assets → READY (all essentials resolved)
  • missing logo/music → suggestions, never blocking; each states fallback + impact
  • more beats than clips → "missing shots" suggestion with recording direction
  • weak (soft/dark) clips flagged from analysis
  • never READY while a mandatory beat is unresolved
backend total: 67 passed; ruff clean; frontend typechecks + builds.
```

## Acceptance gates (doc 19 §8) status
- ✅ Add only a script + raw folder → useful readiness without editing jargon.
- ✅ Every beat marked covered / optional / missing / ambiguous with evidence ids.
- ✅ Never "Ready" while a mandatory shot/fact is unresolved (tested).
- ✅ Never blocks when a safe fallback exists; fallback + impact shown (tested).
- ✅ Missing-footage guidance says what to film, orientation, framing, min duration.
- ✅ Requests resolve via buttons/paths in the UI, not Terminal.
- 🟡 Re-scan clears the resolved request without repeating heavy work — the
  endpoint re-runs quickly (light analysis, capped) but does not yet cache the
  prior scan; caching is the next increment.
- 🟡 Claude as a constrained semantic matcher is scaffolded (deterministic
  baseline ships first); wiring it behind the existing schema-validated provider
  is the follow-up.
