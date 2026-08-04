# Audio DNA + Beat-Synced Campaign Montage — Evidence

Implements pack doc 18 (Reference Quality and Audio DNA): close the gap between
Coach's montage and the owner's real target by cutting **on the music**, laying a
**narrative text story**, tightening pacing, and adding a **branded outro** and a
**consistent mix**.

## Built
- `analysis/audio.py` — Audio DNA: extract audio with FFmpeg, then librosa
  (pinned) derives **tempo, a beat grid, and onsets**. `phrase_cuts_s` returns
  cut points on a ~2 s phrase grid snapped to real beats; `snap_to_onset` keeps a
  cut within a 200 ms window of an onset. librosa optional → fixed grid fallback.
- `montage.py` — beat-synced campaign builder: cuts on the phrase grid, **rotates
  clips for visual variety** (no accidental adjacent duplicates), starts each shot
  on its best moment, reframes on the subject, and lays narrative text beats
  across the shots.
- `render/graph.py` + `render/renderer.py` — the graph now carries a **music bed**
  and an **`Outro`** (logo over a solid background). The renderer decouples video
  and audio concat: a music track becomes the soundtrack (trimmed, faded out,
  **normalised to −14 LUFS / −1 dBTP**), and the branded outro is appended. Clip
  audio is still used (and normalised) when there's no music.
- `autocreate.py` — new `music`, `logo`, `phrase_seconds` options; a supplied
  music track triggers the beat-synced montage + soundtrack, a logo adds the
  outro. New `--music`, `--logo`, `--captions` CLI flags; `music_path`/`logo_path`
  API fields; the app's Create screen gains music/logo/text inputs.

## Verified for real (FFmpeg 7.0.2 + librosa 0.11, this CI run)
- `analyse_audio` on a synthetic 120 BPM click detects ~117–120 BPM with a full
  beat grid; `phrase_cuts_s(2.0)` yields ~2 s cuts snapped to beats.
- `build_music_montage` produces a contiguous timeline with no adjacent duplicate
  shots and captions aligned to shots.
- End-to-end `autocreate --music --logo --captions` renders clean/enhanced/bold:
  1080×1920, beat-timed clips + a 4.5 s branded outro, music soundtrack
  normalised to −14 LUFS, narrative captions burned in.

## Test results
```
backend: 61 passed  (adds audio DNA, montage rotation, music/outro render)
ruff: All checks passed!
frontend: typechecks + builds
```

## Honest scope vs the parity test (doc 18 §7)
Done: beat-synced cuts within a tolerance window, ~2 s phrasing, visual-role
rotation, narrative text beats, branded outro, −14 LUFS non-clipping mix, fully
RenderGraph-driven and reversible, local + zero extra cost.
Not yet: automatic *speech-vs-music* separation and ducking in the same timeline
(hybrid), musical **section/energy** detection (build/drop-aware pacing), and a
formal EBU R128 QC gate on the output. Cuts snap to the beat grid; per-cut
snapping to the nearest *onset* within 200 ms is available (`snap_to_onset`) but
not yet applied inside the montage builder. These are the next increment.
