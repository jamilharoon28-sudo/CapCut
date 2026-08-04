# Phase evidence — Human Judgement Engine, Phase 0 (baseline & foundations)

Per the Human Judgement Engine add-on (§20, Phase 0) and its overriding rule —
*"stop at a phase gate when the evidence is not good enough … never claim a
capability that has not passed its acceptance tests."* This container is Linux
with **no FFmpeg, no macOS (no Apple Vision), no MLX, and none of the owner's
paired footage**, so the acceptance evidence for Phases 1–8 (which is defined in
terms of real sample videos on the M2) cannot be produced here. Phase 0 delivers
the media-independent foundations and the harness the later phases are scored
against; nothing is wired into the live render path, so existing behaviour is
unchanged.

## Delivered (implemented + unit-tested)

`apps/backend/capcut_coach/judgement/`:

- **`schemas.py`** — versioned evidence & decision models with provenance
  (`ShotWindow`, `TechnicalEvidence`, `SubjectEvidence`, `SemanticEvidence`,
  `StoryBeat`, `WindowEvidence`). `SemanticEvidence` is a **closed schema**
  (`extra="forbid"`); `parse_semantic()` returns `None` on any malformed or
  hallucinated payload so callers fall back to Level A (add-on §6, §18).
- **`calibration.py`** — project-relative robust scoring: median/MAD baselines and
  z-scores, plus absolute hard blockers (near-black, severe clipping, frozen).
  Fixes the current "normalise within one clip" flaw and does **not** punish
  intentionally dark footage — only objective faults (add-on §7.3).
- **`story.py`** — script → ordered `StoryBeat`s with **immutable facts**
  (money/percent/offer/URL/number) extracted and marked; CTA/fact beats are
  `required`; `facts_preserved()` guards that shortened wording never drops a fact
  (add-on §8; CLAUDE.md rule 7).
- **`confidence.py`** — HIGH/MEDIUM/LOW → automate / recommend-with-alternatives /
  ask-user policy from calibrated signals, not the model's self-reported number
  (add-on §11).
- **`evaluation.py`** — the private, git-ignored paired-video **manifest format**
  and the 1–5 **rating rubric** (shot_choice, story, pacing, framing, captions,
  audio, overall). The loader refuses any media path that escapes the approved
  roots (path-traversal/symlink guard, add-on §5/§17/§18). Only the schema and
  synthetic fixtures are committed; media stays on the owner's Mac.

Decisions recorded: **ADR-0007** (layered engine, three intelligence levels,
phase gates, Level A always the fallback) and **ADR-0008** (optional local VLM is
advisory, gated, reversible). Planned components + licences catalogued in
`THIRD_PARTY_NOTICES.md` (none vendored yet).

## Test results (this container)

- `tests/test_judgement_phase0.py` — 13 tests, all passing (semantic schema
  rejection, hard blockers, dark-but-usable, project-relative calibration,
  immutable-fact extraction/preservation, confidence policy, manifest path
  safety).
- Full backend: **106 passed, 5 skipped** (FFmpeg-gated), `ruff check capcut_coach`
  clean.

## BLOCKED BY EVIDENCE (needs the M2 Mac + FFmpeg + real footage)

- Phase 0's *measurements* (current shot-selection quality, story coverage, render
  time, peak cache, output size on `bold.mp4` vs `mothersday 1.mp4` and the other
  fixtures) — the harness is defined; the numbers require the Mac + media.
- All of Phases 1–8 and their acceptance gates (window analysis, Apple Vision,
  story optimiser, local VLM, proxy critic/repair, preference learning,
  raw/finished reconstruction, hardening) — to be implemented in order, each
  proven on real footage before the next.

## Not done (by design)

No change to the live `autocreate`/render path; no new runtime dependency added;
no capability claimed as working beyond the pure foundations above.
