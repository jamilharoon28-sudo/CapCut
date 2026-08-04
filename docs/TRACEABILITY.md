# Requirements → Code → Tests Traceability

Covers the add-on requirements (docs 18–19) on top of the base pack. Status: ✅
implemented + tested · 🟡 partial · ⬜ next.

## Doc 18 — Reference Quality & Audio DNA

| Requirement | Code | Test | Status |
| --- | --- | --- | --- |
| Local Audio DNA: tempo, beats, onsets | `analysis/audio.py` | `test_audio_montage::test_analyse_audio_detects_tempo` | ✅ |
| Cuts on a musical phrase grid (~2 s), snapped to beats | `analysis/audio.py::phrase_cuts_s`, `montage.py` | `test_audio_montage::test_phrase_cuts_snap_to_beats` | ✅ |
| Snap a cut to an onset within 200 ms | `analysis/audio.py::snap_to_onset` | (unit via phrase grid) | 🟡 not yet applied per-cut in montage |
| Visual-role variety, no adjacent duplicates | `montage.py` | `test_audio_montage::test_montage_rotates_clips_and_is_contiguous` | ✅ |
| Narrative text-story beats across shots | `montage.py`, `render/ass.py` | render tests | ✅ |
| Music bed as soundtrack, faded, −14 LUFS / −1 dBTP | `render/renderer.py` | `test_audio_montage::test_render_command_music_bed_and_outro` | ✅ |
| Branded outro (logo over background) | `render/graph.py::Outro`, `render/renderer.py` | same as above | ✅ |
| Tighter pacing (median ~2 s, 10–13 blocks) | `montage.py`, `autocreate.py` | end-to-end render | ✅ |
| Hybrid speech+music ducking | — | — | ⬜ |
| Musical section/energy-aware pacing | — | — | ⬜ |
| EBU R128 QC gate on output | `qc.py` (deterministic QC exists) | `test_media_scripts_capcut` | 🟡 loudness gate not yet added |
| Same-footage parity test (sanitised fixture) | — | — | ⬜ |

## Doc 19 — Smart Preflight

| Requirement | Code | Test | Status |
| --- | --- | --- | --- |
| Typed PreflightRequirement/EvidenceMatch/RequestCard/ReadinessReport | `preflight/schemas.py` | `test_preflight` | ✅ |
| Script beats → requirements → evidence match | `preflight/engine.py` | `test_preflight::*` | ✅ |
| READY / READY_WITH_SUGGESTIONS / NEEDS_HELP | `preflight/engine.py` | `test_preflight` (all) | ✅ |
| Block only for material problems | `preflight/engine.py` | `test_missing_logo_and_music_are_suggestions_not_blocking` | ✅ |
| Never READY while a mandatory beat unresolved | `preflight/engine.py` | `test_never_ready_while_a_mandatory_beat_is_unresolved` | ✅ |
| Every card: need/why/recommended/fallback/impact | `preflight/schemas.py::RequestCard` | `test_missing_logo_and_music_...` | ✅ |
| Missing-footage recording directions | `preflight/engine.py` | `test_no_footage_blocks...`, `test_more_beats_than_clips...` | ✅ |
| Readiness UI with request cards, no Terminal | `apps/frontend/.../CreateVideo.tsx` | typecheck + build | ✅ |
| Preflight API endpoint | `routers/create.py::preflight` | (engine-tested) | ✅ |
| Re-scan without repeating heavy work (cache) | — | — | 🟡 |
| Claude as constrained semantic matcher | `claude/` provider exists | — | 🟡 wiring next |
| Learn/reuse stable owner choices | `config.py` (config store exists) | — | ⬜ |

## Doc 20 — Full Autopilot (Music / Footage / Captions)

| Requirement | Code | Test | Status |
| --- | --- | --- | --- |
| Rights-gated Approved Music library (content-hash + Audio DNA) | `music/library.py`, `music/schemas.py` | `test_music_autopilot::test_only_rights_eligible_...` | ✅ |
| Only rights-eligible tracks auto-selectable | `music/schemas.py::MusicAsset.eligible`, `select.py` | `test_only_rights_eligible_tracks_are_selectable` | ✅ |
| Reproducible selection + two alternatives + reason | `music/select.py` | `test_selection_is_reproducible_and_offers_alternatives` | ✅ |
| Dialogue edits avoid vocal tracks | `music/select.py` | `test_dialogue_edit_avoids_vocal_tracks` | ✅ |
| No network / music-ripping code path | `music/*` (by design) | `test_music_module_has_no_network_or_download_code` | ✅ |
| Missing music never blocks a viable edit | `preflight/engine.py`, `autocreate.py` | `test_preflight::test_missing_logo_and_music_...` | ✅ |
| Automatic best-candidate selection (AutopilotDecision) | `autopilot/select.py`, `schemas.py` | `test_choose_best_prefers_richer_candidate` | ✅ |
| Make My Video renders only the chosen best | `autocreate.py` (`make_my_video`), `routers/create.py` | end-to-end (evidence) | ✅ |
| Music bed mixed to −14 LUFS / −1 dBTP, faded | `render/renderer.py` | `test_audio_montage::test_render_command_music_bed_and_outro` | ✅ |
| One-screen Make My Video UI | `apps/frontend/.../CreateVideo.tsx`, `api.ts` | typecheck + build | ✅ |
| Automatic dialogue ducking (sidechain) | — | — | 🟡 |
| Global footage optimiser: 2 alternatives per beat + swap | `montage.py` (rotation) | — | 🟡 |
| Grouped factual review (low-confidence names/prices/dates) | — | — | 🟡 |
| Trusted Autopilot after 5 safe jobs | — | — | 🟡 |
| Word-level captions monotonic/in-bounds/non-overlapping | `media/srt.py`, `talking.py` | `test_media_scripts_capcut::test_srt_*` | ✅ |

## Safety invariants (unchanged, still enforced)
Loopback + bearer token; path-safety / cloud read-only; no fabricated
footage/claims/logos; local + zero-additional-cost (no Remotion / paid APIs);
CapCut-optional. Covered by `test_security`, `test_jobs_and_api`, and the
render/preflight suites.
