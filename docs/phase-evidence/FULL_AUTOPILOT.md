# Full Autopilot — Evidence (pack doc 20)

One-button **Make My Video**: Coach auto-selects footage moments, auto-selects a
**rights-approved** track, renders the final, and auto-picks the best candidate —
the owner reviews rather than edits. Additive; nothing prior was removed.

## Built
- `music/schemas.py` — `MusicAsset` (+ `RightsStatus`) and `MusicSelection`. Only
  `OWNER_APPROVED` / `SHIPPED_LICENSED` tracks are `eligible`.
- `music/library.py` — index an owner-approved music folder by content hash +
  Audio DNA (bpm/energy/duration). Cloud/synced folders refused. Records a rights
  note from a sibling `RIGHTS.txt` when present. **No network/download code.**
- `music/select.py` — deterministic, reproducible scoring (duration adequacy,
  energy match, tempo preference, vocals-vs-dialogue) → best + two alternatives +
  a plain-language reason.
- `autopilot/schemas.py` + `select.py` — `AutopilotDecision`; scores the
  Clean/Enhanced/Bold graphs (coverage, captions, soundtrack, branded ending,
  grade, minus deterministic QC penalties) and picks the highest safe one
  (ties → conservative Enhanced).
- `autocreate.py` — `approved_music_roots` auto-picks a track when none is given;
  `make_my_video=True` scores the graphs and renders **only** the chosen one.
  New `--music-library`, `--make-my-video` CLI flags; `config` gains
  `approved_music_roots`.
- API `POST /projects/{id}/make-my-video`; UI gains **Make My Video** (autopilot)
  alongside **Review 3 versions**, plus a Music-folder input.

## Verified (FFmpeg 7.0.2 + librosa, this CI run)
- End-to-end `--music-library --make-my-video`: Coach indexed the approved folder,
  selected the track, chose **enhanced**, and rendered **only that** candidate
  (10.2s, with the auto-selected soundtrack).
- `test_music_autopilot.py` — 6 passed: rights gate excludes ineligible tracks;
  selection is reproducible + offers alternatives; dialogue edits avoid vocals;
  empty library returns None (not an error); **the music package contains no
  network/ripping tokens** (requests/urllib/http/youtube/spotify/tiktok/yt-dlp/
  socket/…); autopilot prefers the richer candidate.
- Backend total **73 passed**; ruff clean; frontend typechecks + builds.

## Doc-20 acceptance gates status
- ✅ Make My Video produces a final MP4 with no manual timeline editing, local,
  CapCut-optional, zero extra cost.
- ✅ Only rights-eligible indexed tracks selectable; reproducible + 2 alternatives.
- ✅ No network/music-ripping path reachable (tested).
- ✅ Missing music doesn't block — Smart Preflight offers choices; clean/silent
  edit is viable.
- ✅ Final selection scored deterministically; renders only the best (no wasted
  full-res renders).
- 🟡 Automatic **dialogue ducking** of music (speech leads) — mix normalises and
  fades today; sidechain ducking is the next increment.
- 🟡 Global footage-sequence optimiser keeps *two* labelled alternatives per beat
  — current rotation avoids adjacent duplicates; explicit per-beat alternatives +
  "Change this clip" swap are next.
- 🟡 Grouped factual review for low-confidence names/prices/dates — captions come
  from real words; the confidence-grouping review card is next.
- 🟡 Trusted Autopilot after 5 safe jobs — Make My Video ships day one with
  conservative defaults; the learned-autonomy unlock is a follow-up.
