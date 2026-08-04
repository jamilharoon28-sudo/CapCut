# Phase evidence — Editorial controls & trusted autopilot (increments #2–#4)

Three post-render refinements that keep the beginner in control while Coach does
the heavy lifting. All engine logic is pure, deterministic, and unit-tested with
no FFmpeg/disk dependency; the render/re-render paths reuse the existing tested
pipeline.

## Increment #2 — Per-beat clip alternatives + "Change this clip"

- `editing/slots.py` — `build_slots` lists each timeline slot with ranked
  alternative clips that can cover the slot's exact duration (so a swap never
  shifts timing); neighbours are excluded to preserve visual variety.
  `replace_slot` rebuilds one slot from a chosen clip (best moment + subject
  reframe), leaving position, length, and every other slot untouched. Pure — the
  input plan is deep-copied, never mutated.
- Persisted at render time: `autocreate` now writes `plan.json`, `catalog.json`,
  `analyses.json`, and `render_context.json` next to the candidates, so swaps and
  re-renders need no re-analysis. `rerender_from_plan` re-renders the three
  candidates from the (possibly edited) plan.
- Endpoints: `GET /projects/{id}/slots`, `POST /projects/{id}/slots/{i}/replace`
  (persists the edited plan, enqueues a re-render job).
- UI: a "Change a clip" panel on Review lists shots and offers alternative chips;
  choosing one swaps and re-renders, returning to Review.
- Tests: `test_editing_slots.py`, `test_editing_api.py`, and a CreateFlow case.

## Increment #3 — Grouped factual review before publish

- `editing/review.py` — `build_review_groups` turns the finished plan into a short
  grouped checklist: on-screen text claims (each requires acknowledgement — Coach
  never invents facts), low-confidence/flagged shots (advisory), music rights
  (required when a track is used), and branding (advisory). `required_ack_ids`
  lists what must be ticked.
- Enforcement: `POST /projects/{id}/approve` refuses (409 `review_incomplete`,
  with the missing ids) until every required item is acknowledged. Honours
  CLAUDE.md rule 14 — Coach never treats an edit as publish-ready on its own.
- Endpoint: `GET /projects/{id}/review`.
- UI: a "Before you save" checklist on Review; Save is disabled until required
  items are confirmed, and the acknowledged ids are sent to approve.
- Tests: `test_editing_review.py`, `test_editing_api.py`, and a CreateFlow case.

## Increment #4 — Trusted one-tap autopilot after earned approvals

- `approvals.py` + migration v2 (`approvals` table) — every approval (manual or
  auto) is logged. `trust_state` reports the count and whether one-tap has
  unlocked (default threshold: 5 approved videos). "Automatic" is earned, never
  assumed.
- Gating: `make-my-video` honours `auto_save` only when the threshold is met AND
  a **local** default output folder is set; otherwise the video is still rendered
  for manual review. Auto-save copies the best candidate to the local folder,
  records the approval, and never touches originals or cloud (safety rules 1, 12).
- Endpoints: `GET /system/trust`, `POST /system/default-output` (rejects cloud
  paths).
- UI: Create shows "Make & save automatically" only when one-tap is ready, with a
  progress hint otherwise; Settings has the local save-folder control.
- Tests: `test_trust_autopilot.py`, and a CreateFlow case.

## Results (CI, Linux container — no CapCut/Mac)

- Backend: 90 passed, 5 skipped (FFmpeg-gated), `ruff check capcut_coach` clean.
- Frontend: 21 passed, `tsc --noEmit` clean, production build succeeds (~56 KB gz).
- **BLOCKED BY EVIDENCE:** end-to-end swap/re-render, auto-save copy, and the Mac
  `.zip`/folder picker require the M2 Mac + FFmpeg and are recorded as such until
  run on the owner's machine.

## Related fixes in this change

- The "Review 3 versions" (`autocreate`) endpoint now accepts a `.zip` of clips,
  matching `make-my-video`, the CLI, and preflight.
- The macOS folder picker now allows selecting a `.zip` of clips as well as a
  folder.

## Wide-format & real-world footage robustness

Prompted by real `.mov` footage failing to render:

- **Many more containers accepted.** `VIDEO_EXTS` expanded from 5 to ~25
  (`.webm`, `.mts`/`.m2ts`, `.3gp`, `.wmv`, `.flv`, `.mpg`, `.ts`, `.mxf`, …).
- **Sturdier probing.** `_probe` now reads structured ffprobe JSON, falling back
  from format duration to the video-stream duration, so more files yield a usable
  duration instead of being silently dropped.
- **Rotation baked in correctly.** Phone `.mov` clips store portrait video as
  landscape + a rotate flag; under `-filter_complex` FFmpeg does **not**
  auto-apply it, which produced sideways/zoomed frames. Coach now probes the
  rotation (rotate tag or display-matrix), passes `-noautorotate` per input for
  version-stable behaviour, and prepends the matching `transpose` so clips come
  out upright before scale/crop. Rotation is persisted so swaps/re-renders keep it.
- **Real errors surface.** The job payload now carries `error_detail`, and the
  Create error screen shows a "Technical details" disclosure with the actual
  FFmpeg message — so a genuine failure is diagnosable instead of a generic note.
- Tests: `test_video_formats.py` (format breadth + rotation normalisation) and a
  `test_render.py` case asserting rotated clips get `transpose` + `-noautorotate`.
  End-to-end rendering of real rotated `.mov` remains **BLOCKED BY EVIDENCE**
  until run on the Mac with FFmpeg.
