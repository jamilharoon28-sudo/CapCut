# API, Configuration and Storage Contract

This file makes the implementation concrete while allowing Claude Code to refine field names through migrations and generated schemas.

## 1. Local filesystem layout

Use macOS-standard locations and discover the actual home path at runtime. Never embed a user's absolute path in source, tests or logs.

```text
~/Library/Application Support/CapCut Coach/
├── coach.sqlite3
├── config.json
├── auth-token
├── models/
├── style-dna/
├── asset-packs/
├── backups/
├── projects/
│   └── <coach-project-id>/
│       ├── manifests/
│       ├── scripts/
│       ├── learning-capsule/
│       ├── previews/
│       ├── captions/
│       ├── selected-clips/
│       ├── handoff/
│       └── reports/
└── compatibility/

~/Library/Caches/CapCut Coach/
├── proxies/
├── audio/
├── thumbnails/
├── transcripts/
└── claude-decisions/

~/Library/Logs/CapCut Coach/
└── coach.log
```

Do not place backups inside CapCut's project directory. A corrupted/broad cleanup there must not remove Coach recovery copies.

## 2. Configuration

`config.json` should be written through typed settings, not hand-edited. Suggested keys:

```json
{
  "schema_version": 1,
  "approved_media_roots": [],
  "capcut_project_roots": [],
  "export_roots": [],
  "processing_mode": "balanced",
  "pause_on_battery": true,
  "pause_heavy_work_while_capcut_open": true,
  "minimum_free_space_gb": 30,
  "minimum_free_space_percent": 15,
  "cache_budget_gb": 40,
  "source_cleanup_policy": "ask_after_verified_completion",
  "source_cleanup_destination": "macos_trash",
  "retain_approved_finals": true,
  "retain_scripts": true,
  "retain_learning_capsules": true,
  "whisper_model": "auto-benchmarked",
  "language": "en",
  "claude_enabled": true,
  "claude_paid_overage_enabled": false,
  "screen_help_enabled": false,
  "accessibility_automation_enabled": false,
  "direct_capcut_write_enabled": false,
  "active_style_dna_version": null,
  "active_asset_pack_id": null
}
```

Secrets/tokens never go in this JSON. Store them in Keychain where practical or a mode-0600 file.

## 3. Local API rules

- Base: `http://127.0.0.1:<assigned-port>/api/v1`.
- Bind loopback only.
- Require local bearer token and same-origin protections.
- JSON request/response except streamed preview/media routes.
- OpenAPI generated from typed models.
- Every mutation accepts/returns an idempotency key where a duplicate action would be harmful.
- Long operations return a persisted job id.
- Errors include stable code, simple user message and optional Advanced detail.

## 4. Endpoint outline

### System

- `GET /system/status`
- `POST /system/doctor`
- `GET /system/permissions`
- `POST /system/permissions/open-settings`
- `GET /system/storage`
- `POST /system/cache/cleanup`

### Projects

- `GET /projects`
- `POST /projects`
- `GET /projects/{id}`
- `PATCH /projects/{id}`
- `DELETE /projects/{id}/analysis`
- `POST /projects/{id}/ingest`
- `POST /projects/{id}/plan`
- `POST /projects/{id}/approve-plan`
- `POST /projects/{id}/render-preview`
- `POST /projects/{id}/prepare-capcut`
- `GET /projects/{id}/cleanup-preview`
- `POST /projects/{id}/finish-and-free-space`
- `GET /projects/{id}/learning-capsule`

### Media/transcript

- `GET /projects/{id}/media`
- `GET /media/{id}/metadata`
- `GET /media/{id}/proxy`
- `GET /media/{id}/waveform`
- `GET /media/{id}/contact-sheet`
- `GET /projects/{id}/transcript`
- `PATCH /transcript/words/{id}`

### Scripts

- `POST /projects/{id}/scripts/import`
- `GET /projects/{id}/scripts`
- `GET /projects/{id}/shot-plan`
- `PATCH /projects/{id}/shot-plan/{node_id}`
- `POST /projects/{id}/shot-plan/match-media`

### Edit candidates

- `GET /projects/{id}/edit-candidates`
- `GET /edit-candidates/{id}`
- `POST /edit-candidates/{id}/change-hook`
- `POST /edit-candidates/{id}/adjust-pace`
- `POST /edit-candidates/{id}/restore-unit`
- `POST /edit-candidates/{id}/approve`

### Dataset/style

- `POST /dataset/examples/import`
- `GET /dataset/examples`
- `PATCH /dataset/examples/{id}`
- `POST /dataset/examples/{id}/analyse`
- `POST /style-dna/build-candidate`
- `GET /style-dna/versions`
- `GET /style-dna/versions/{id}`
- `POST /style-dna/versions/{id}/approve`
- `POST /style-dna/versions/{id}/rollback`
- `POST /preferences/ab-choice`

### CapCut

- `GET /capcut/status`
- `POST /capcut/discover`
- `POST /capcut/diagnose`
- `GET /capcut/compatibility`
- `POST /capcut/canary`
- `POST /capcut/projects/{coach_project_id}/handoff`
- `POST /capcut/projects/{coach_project_id}/clone-template`
- `POST /capcut/backups/{id}/restore`
- `POST /capcut/open`

### Guidance

- `GET /projects/{id}/guidance/current`
- `POST /projects/{id}/guidance/{step_id}/done`
- `POST /projects/{id}/guidance/{step_id}/stuck`
- `POST /projects/{id}/guidance/{step_id}/automate`
- `POST /guidance/emergency-stop`

### Exports/QC

- `GET /exports/recent`
- `POST /exports/{id}/match`
- `POST /exports/{id}/review`
- `GET /qc-results/{id}`
- `POST /qc-findings/{id}/resolve`
- `POST /qc-findings/{id}/ignore`
- `POST /exports/{id}/approve-final`
- `POST /exports/{id}/learn`

### Jobs

- `GET /jobs`
- `GET /jobs/{id}`
- `POST /jobs/{id}/cancel`
- `POST /jobs/{id}/retry`
- `GET /jobs/{id}/events` using server-sent events

## 5. Internal edit-plan contract

Use integer microseconds or rational time, not floating-point seconds, in persisted edit data.

```json
{
  "schema_version": 1,
  "id": "edit_uuid",
  "project_id": "project_uuid",
  "style_dna_version": "style_uuid",
  "canvas": {"width": 1080, "height": 1920, "fps_num": 30, "fps_den": 1},
  "segments": [
    {
      "id": "seg_uuid",
      "asset_id": "asset_uuid",
      "source_start_us": 0,
      "source_duration_us": 2000000,
      "timeline_start_us": 0,
      "timeline_duration_us": 2000000,
      "role": "hook",
      "reason": "strong_problem_statement",
      "confidence": 0.91,
      "transform": {"scale": 1.0, "x": 0.0, "y": 0.0},
      "must_review": false
    }
  ],
  "captions": [],
  "audio_tracks": [],
  "broll": [],
  "graphics": [],
  "warnings": []
}
```

Every adapter translates from this contract. Do not let CapCut-specific ids leak into editorial planning.

## 6. Job contract

Job fields:

- id, type, project id;
- state: queued/running/paused/succeeded/failed/cancelled;
- stage and percent where measurable;
- created/started/finished timestamps;
- attempt count and max attempts;
- input fingerprint;
- output artifact ids;
- stable error code and redacted detail;
- cancellation requested flag;
- heartbeat and worker identity.

Heavy jobs are serialised. Light metadata/QC jobs may run concurrently if they do not compete with CapCut.

## 7. File stability contract

A watched file is ready only when:

- it still exists;
- size and mtime remain unchanged through the configured quiet period;
- it can be opened for reading;
- ffprobe succeeds where applicable;
- for CapCut project files, valid JSON/envelope parsing succeeds and relevant sibling files are also stable;
- for exports, duration is non-zero and no writer holds it where detectable.

## 8. Versioning

Version independently:

- database schema;
- edit-plan schema;
- Style DNA schema;
- Claude prompt/schema bundles;
- CapCut adapter/compatibility entries;
- guidance knowledge maps;
- master templates;
- asset packs.

Every generated project/report records all relevant versions for reproducibility.

## 9. Backup retention

- Original-project backup snapshots are never auto-deleted by generic cache cleanup.
- Coach-generated project backups may use a configurable retention count, default 10 versions/project.
- Database automatic backup before migrations and before Style DNA destructive operations.
- Display backup age/size and provide deliberate cleanup.

## 9A. Source-media cleanup contract

`GET /projects/{id}/cleanup-preview` returns the exact candidate items, canonical paths, hashes, total bytes, shared-reference blockers, retention choice and prerequisites. It never mutates.

`POST /projects/{id}/finish-and-free-space` requires a fresh preview token, explicit retention choice and typed confirmation. It is idempotent and journals each exact file move. Only verified standalone local source files inside approved roots may move to macOS Trash. CapCut Cloud/account/Space, Google Drive and mounted/synchronised cloud paths are always ineligible. Folder recursion, glob targets, symlink traversal, permanent deletion and Trash-emptying are forbidden.

Cleanup remains blocked until the approved final is playable and hashed, the learning capsule is committed/checksummed, relevant jobs are complete and shared hashes are resolved. A partial cleanup is reported item by item and remains resumable.

## 10. Observability

Logs should answer:

- which stage ran;
- which content/config fingerprints were used;
- why a cache hit/miss occurred;
- why a CapCut write was allowed/refused;
- which adapter/version was selected;
- whether Claude was called and which prompt version, without logging sensitive transcript by default;
- how long each stage took;
- what recovery action is available.

The UI translates errors into plain language while Advanced exposes an exportable redacted diagnostic bundle.
