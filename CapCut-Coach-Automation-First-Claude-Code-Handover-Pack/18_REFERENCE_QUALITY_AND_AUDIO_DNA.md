# Reference Quality and Audio DNA

## 1. Purpose

This file converts the owner's real reference videos into measurable build requirements. `bold.mp4` is the current Coach output. `mothersday 1.mp4` is the primary target because it uses the same underlying treatment footage. `9th April 2026 8PM(1).mp4` is a secondary target showing the same human editor's wider montage style.

The private client files are evaluation evidence only. Never commit, bundle, upload, redistribute or extract reusable client assets from them. Build sanitised synthetic fixtures with equivalent structure.

## 2. Measured comparison

Measurements were taken from the supplied final files using ffprobe, scene-change analysis, EBU R128 loudness analysis and local spectral-onset analysis. Scene detection is an approximation; preserve the raw reports when implementing the formal evaluator.

| Attribute | Current `bold.mp4` | Primary target `mothersday 1.mp4` | Secondary target `9th April…` |
|---|---:|---:|---:|
| Duration | 25.4 s | 29.0 s | 16.6 s |
| Delivery | 1080×1920 H.264 | 2160×3840 HEVC | 2160×3840 HEVC |
| Detected cuts | 7 | 11 | 11 |
| Timeline blocks | 8 | 12 | 12 |
| Average block | 3.17 s | 2.41 s | 1.38 s |
| Median block | 3.76 s | 2.02 s | 1.32 s |
| Rough soundtrack pulse | 83 BPM | 120 BPM | 123 BPM |
| Cuts within 200 ms of a detected audio onset | 6/7 | 11/11 | 10/11 |
| Integrated loudness | -15.4 LUFS | -16.5 LUFS | -12.5 LUFS |
| Loudness range | 16.1 LU | 0.4 LU | 6.4 LU |
| Visible narrative text | None in sampled frames | Campaign copy throughout | Minimal/none in sampled frames |
| Branded outro | Missing | Approximately 5 s animated logo outro | Approximately 2.2 s logo outro |

The primary target is not better because it is 4K. It is better because it has a coherent message, stronger shot coverage, disciplined phrase timing, typographic hierarchy, campaign context and a designed ending.

## 3. What the Mothers' Day editor actually did

The same raw visual world became a campaign story:

1. establish equipment with **A Moment For Mum**;
2. show the client with **To relax**;
3. show the practitioner with **To glow**;
4. continue care imagery with **to feel beautiful**;
5. change angle with **to be taken care of**;
6. return to equipment/client with **just like she deserves**;
7. introduce **Mother's Day** over a treatment detail;
8. use additional proof/detail/product/treatment shots;
9. resolve with a designed Beauty in the City logo animation.

Most editorial blocks sit on an approximately two-second grid, with one four-second phrase and a five-second branded ending. Repetition is purposeful: operator, client, equipment and close detail alternate to prevent visual fatigue.

`bold.mp4` contains usable footage but lacks this semantic layer. Its eight blocks are mostly long, literal and sequential. It has no visible campaign copy or branded resolution, and its audio has much wider level variation. Calling it **Bold** does not make it editorially bold.

## 4. Required Audio DNA engine

Audio understanding is mandatory even when music selection itself is optional.

### Analysis

For every audio source, locally derive:

- speech/music/sound-effect regions;
- word timestamps and voice-activity confidence;
- integrated loudness, loudness range, sample/true peak and silence;
- tempo candidates, beat/downbeat grid and onset strengths;
- musical sections, energy curve, builds, drops and ending cadence;
- transient events suitable for a cut, text reveal or restrained transition;
- clipping, discontinuity, phase/channel and noise warnings.

Use free local components: FFmpeg/ffprobe filters for extraction, EBU R128 and mixing; whisper.cpp/VAD for speech; and a pinned open-source onset/beat implementation such as librosa or aubio. No paid music-analysis API is permitted.

### Planning

- Dialogue-led video: speech meaning and natural breath boundaries lead; music follows and ducks.
- Montage-led video: music phrases/downbeats lead, but shot meaning and visibility remain hard constraints.
- Hybrid video: lock speech first, then place visual changes and accents at safe musical onsets.
- Snap an intended cut to a strong onset only inside an allowed timing window; never clip a word, action or required result merely to hit a beat.
- Choose the beat subdivision that matches the target style. For the Mothers' Day playbook, begin with two-second phrases around a 120 BPM track rather than cutting every beat.
- Use sound effects only from user-owned/approved local assets. A clean edit without an effect is the fallback.

### Mixing

- Preserve intelligible speech and use automatic ducking when speech exists.
- Use short equal-power crossfades at audio edits to prevent clicks.
- Normalise to a configurable social target; begin testing around -14 LUFS integrated and no higher than -1 dB true peak, then learn the owner's approved range.
- Do not copy the reference's 0 dB peaks merely because they exist; target the same perceived confidence with safer headroom.
- Keep montage music consistent through the body and design the final cadence/fade around the outro.

## 5. Reference DNA schema

Store derived style without retaining copyrighted audio or client frames:

```json
{
  "format": "campaign_service_montage",
  "duration_band_s": [25, 32],
  "shot_duration_median_s": 2.02,
  "shot_duration_pattern": [2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 5],
  "visual_roles": ["equipment", "client", "practitioner", "detail", "product", "treatment", "outro"],
  "text_story_required": true,
  "text_phrase_count_band": [5, 8],
  "brand_outro_s": [4, 5.5],
  "tempo_preference_bpm": [115, 125],
  "cut_onset_tolerance_ms": 200,
  "mix_target_lufs": -14,
  "source": "owner_approved_derived_metrics_only"
}
```

This is a playbook prior, not a universal hard rule. A talking-head script, testimonial or different campaign may need different pacing.

## 6. Script-to-story requirements

The planner must transform a script or campaign brief into:

- mandatory facts and claims;
- hook/promise;
- emotional progression;
- short on-screen copy beats;
- visual role required for each beat;
- CTA/brand resolution;
- audio phrase and reveal plan.

If the script lacks short overlay copy, Coach may propose it but must preserve meaning and require approval for a new offer, medical/result claim, price or factual statement. Typography must use the current asset pack's approved fonts, colours, casing, safe zones and emphasis rules.

## 7. Same-footage parity test

Create a sanitised Mothers' Day-style fixture containing equivalent shot roles and a harmless fictional brief. From raw footage plus script only, Enhanced/Bold must:

- create 10–13 purposeful timeline blocks in a 27–31-second campaign;
- keep median body-shot duration between 1.8 and 2.3 seconds unless the audio/story justifies otherwise;
- use at least five distinct visual roles and avoid accidental adjacent duplicates;
- create 5–8 readable narrative text beats that form a complete message;
- place at least 85% of montage cuts within 200 ms of a valid musical onset/phrase boundary;
- include a 4–5.5-second branded outro when supplied assets/script require it;
- achieve a stable, non-clipping mix and pass EBU R128/QC checks;
- remain editable at the RenderGraph level, with every text, clip, cut snap and audio decision reversible;
- render locally without CapCut, a paid API or copyrighted reference media.

Do not require pixel similarity. Judge narrative function, pacing, audio synchronisation, typography, visual-role coverage and brand completion.

## 8. Required owner assets and honest limits

To reach the target reliably, the job should include:

- script/campaign brief;
- raw footage with enough distinct shot roles and stable usable ranges;
- transparent logo and, ideally, a short approved outro asset;
- brand colours/fonts or permission to use a clean default;
- an owned/licensed music track or approved local royalty-cleared library.

Coach cannot truthfully manufacture a missing treatment angle, result, practitioner, logo or claim. It may crop/reframe, create motion from a still range, propose text and build a generic outro, but missing evidence must be shown as a simple request or conservative fallback.
