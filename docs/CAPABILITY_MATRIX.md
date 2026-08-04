# Capability Matrix — what the UI may honestly claim

Derived by inspecting every backend route and the frontend API client. The
redesign uses this to stay truthful: no button appears unless its backend exists.

## ✅ Working now (local, no extra setup)
| Capability | Endpoint(s) | Notes |
| --- | --- | --- |
| Create 3 candidates (Clean/Enhanced/Bold) | `POST /projects/{id}/autocreate` → job → `GET /projects/{id}/candidates` | renders local MP4s, served at `/previews` |
| Make My Video (auto-pick best) | `POST /projects/{id}/make-my-video` | renders only the chosen candidate |
| Smart Check (readiness) | `POST /projects/{id}/preflight` | Needed / Suggestions in plain language |
| Best-moment + subject reframe | (in render engine) | automatic |
| On-screen campaign text | autocreate `captions` | script-led text, one line per shot |
| Branded outro | autocreate `logo_path` | when a logo image is provided |
| Loudness / true-peak QC | (in autocreate; `qc` on each result) | EBU R128 −14 LUFS gate |
| Projects CRUD | `GET/POST /projects`, `GET/PATCH /projects/{id}`, `DELETE /projects/{id}/analysis` | analysis-only delete; originals untouched |
| System doctor / storage | `POST /system/doctor`, `GET /system/storage`, `GET /system/status` | friendly Settings |
| Job status + progress | `GET /jobs/{id}` (`stage`, `percent`) | real progress, no fakes |

## 🟡 Working with local assets / one-time setup
| Capability | Requires | Endpoint |
| --- | --- | --- |
| Beat-synced music + soundtrack | a music track, or an Approved Music folder | autocreate `music_path` / config `approved_music_roots` |
| Automatic music selection | an Approved Music folder set in config | `make-my-video` uses `approved_music_roots` |
| Speech captions + dialogue ducking | whisper.cpp model (`scripts/setup-whisper.sh`) | talking mode inside autocreate |

## ⛔ Not implemented — the UI must NOT claim these
| Capability | Status | UI treatment |
| --- | --- | --- |
| Google Drive connector | not implemented | Connections shows local only; no Drive button |
| "Open in CapCut" handoff | builder exists, **no endpoint/flow** | omit until wired; label "optional, later" |
| Style-DNA learning ingestion (15–20 examples) | not implemented | My Style: honest "starts smart, learns over time" |
| Job cancellation honored mid-render | `/jobs/{id}/cancel` sets a flag the worker doesn't check | do **not** show a Cancel that stops work |

## Gaps this redesign closes with the smallest safe backend additions
| Gap | New endpoint | Safety |
| --- | --- | --- |
| Record the chosen candidate / save output | `POST /projects/{id}/approve` (+ optional copy to a destination) | copies the chosen MP4 to a user-chosen local folder; never touches originals |
| Clean only Coach cache/temp, with confirmation | `POST /system/cache/cleanup` (+ `GET /system/cache/size`) | acts only on the Coach cache dir; reports bytes; requires an explicit confirm token |
| Native Mac folder/file pickers | mac-app `WKScriptMessageHandler` → `NSOpenPanel` | scoped to the local UI; returns only the chosen path |
