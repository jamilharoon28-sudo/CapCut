# Dataset and Universal Style-Learning Guide

## 1. Purpose

The system learns one main editor fingerprint across brands. Brand assets remain separate. The training dataset must therefore contain examples that genuinely share the style the user wants Coach to reproduce.

Do not describe this as “training Claude on videos.” Most of the useful learning is deterministic alignment, measurement, example retrieval and a transparent preference profile.

## 2. Recommended amount

- 5 paired examples: pipeline proof only.
- 10 examples: first useful profile.
- 15–20 examples: recommended initial Style DNA.
- 25–30 examples: stronger coverage and held-out testing.
- More than 40: only valuable if quality remains consistent and new examples add meaningful variety.

Quality and correct pairing matter more than volume.

## 3. Ideal contents per example

```text
example-001/
├── raw/
│   ├── camera-a-001.mov
│   ├── camera-a-002.mov
│   └── broll-001.mov
├── scripts/
│   ├── campaign-scripts.docx
│   └── recording-instructions.docx
├── final/
│   └── approved-final.mp4
├── capcut-project/               # optional but highly valuable
├── intermediate-exports/         # optional
├── captions.srt                  # optional
├── reference/                    # optional reference supplied to editor
├── assets/                       # optional logo/fonts/CTA used
└── example.json
```

Suggested `example.json`:

```json
{
  "title": "Example 001",
  "quality": "excellent",
  "approved": true,
  "editor": "main-editor",
  "content_type": "talking-head-educational",
  "language": "en",
  "notes": "Strong pacing and captions. Copy this style.",
  "must_not_learn": [],
  "rights_confirmed": true
}
```

The UI should create this metadata; the user should not edit JSON manually.

## 4. Import wizard

For every pair, ask only:

1. Which file/ZIP contains the script and recording instructions?
2. Which folder contains all raw footage used or considered?
3. Which file is the approved finished video?
4. How good is this example? Excellent / Good / Average / Do Not Copy.
5. Is the original CapCut project available locally or through the user's CapCut Space?
6. Is there anything Coach should not learn from this example?

Autodetect likely pairs by filename, duration, creation date and audio match, but require confirmation.

Support `.docx`, `.pdf`, `.txt`, `.md` and safe ZIP bundles. Parse reel/shot numbers, time ranges, camera directions, dialogue, overlays, cutaways, transitions, pacing and end cards; music fields are optional. Preserve original order and cross-references between reusable shots. Show the parsed structure before analysis and allow corrections.

## 5. Dataset validation

Before analysis:

- verify the final file opens and has audio where expected;
- verify raw media opens;
- hash everything;
- detect duplicate examples;
- detect whether the final is longer than all plausible raw sources;
- warn when raw footage appears incomplete;
- warn if final and raw audio have no detectable relationship;
- detect watermarks/burned captions where possible;
- detect if an example is radically different in length/format/style;
- never fail the whole dataset because one example is bad.

Each example receives one status:

- `READY`
- `PARTIAL_RAW`
- `CAPCUT_PROJECT_UNREADABLE`
- `LOW_ALIGNMENT_CONFIDENCE`
- `DUPLICATE`
- `EXCLUDED`

## 6. Raw-to-final matching algorithm

### Stage A: audio preparation

- Extract mono 16 kHz audio from every raw and final asset.
- Normalise only for analysis; do not modify sources.
- Use VAD to locate speech.
- If music obscures final speech and matching fails, optionally introduce a voice-separation experiment; do not make heavy separation a default dependency.

### Stage B: candidate matching

- Compute windowed MFCC/chroma or landmark fingerprints.
- Search each final window across raw assets.
- Retain multiple candidates with similarity scores.
- Use transcript word sequences as a second signal.

### Stage C: sequence alignment

- Use dynamic programming/DTW to favour chronological coherent source sequences while allowing editor reordering.
- Detect repeated takes that share similar words but differ in time.
- Refine each boundary with waveform cross-correlation.

### Stage D: visual verification

- Compare perceptual hashes/feature descriptors at proposed corresponding frames.
- Estimate crop/scale/translation where possible.
- Reject audio matches contradicted by strong visual evidence unless the final intentionally uses B-roll.

### Stage E: exact project data

If a readable original CapCut project is supplied, extract exact source mappings, text, timing and effect metadata. Treat this as higher-confidence evidence than inference, after validating referenced media hashes.

## 7. Style DNA schema

The JSON schema should contain:

```text
metadata
  version
  created_at
  approved_at
  example_ids
  total_weight

selection
  restart_policy
  filler_policy
  semantic_completeness
  preferred_hook_features

pacing
  opening_delay_distribution
  shot_length_distribution
  pre_roll_distribution
  post_roll_distribution
  pause_retention_distribution

captions
  words_per_caption
  characters_per_line
  line_count
  duration
  reading_speed
  vertical_position
  highlight_rate
  casing_and_punctuation

framing_motion
  crop_distribution
  subject_position
  punch_in_frequency
  punch_in_scale
  animation_duration

broll
  frequency
  duration
  relation_to_speech
  repetition_tolerance

audio
  speech_loudness
  music_to_speech_delta
  fade_duration
  sound_effect_frequency

transitions
  cut_rate
  allowed_types
  duration

cta
  start_offset_from_end
  duration
  density

confidence
  per_section
  conflicts
  unsupported_inferences

manual_overrides
  separate_from_learned_values
```

## 8. Aggregation

- Excellent weight: 1.0.
- Good weight: 0.65.
- Average weight: 0.25.
- Do Not Copy weight: excluded from positive statistics; store negative features where interpretable.

Weights are defaults and must be configurable. Use robust medians, quantiles and trimmed distributions. Never let one unusually edited video dominate.

If a feature has insufficient evidence, set it to `unknown` and use a conservative default. Do not invent a preference.

## 9. One universal style, not brand models

Style DNA is universal. Projects may still supply an **asset pack**:

- logo;
- primary/secondary colours;
- font names/files;
- CTA copy;
- disclaimer text;
- safe assets.

Content type may influence structural requirements—for example, an advertisement needs a CTA—but it must not silently create a new brand style profile.

## 10. Readable learned-profile screen

Show findings such as:

> Coach studied 18 approved examples. The editor usually begins speech quickly, keeps short natural pauses, uses mostly straight cuts, adds a modest punch-in around important claims, keeps captions concise, and introduces B-roll periodically rather than continuously.

Then show measurable evidence:

- median opening delay;
- common shot-length range;
- caption words/line;
- zoom frequency/range;
- B-roll frequency/range;
- CTA duration;
- confidence and conflicting examples.

Allow **Correct this**, **Ignore this feature**, and **Approve Style**.

## 11. Using the profile on new footage

1. Retrieve 3–5 similar approved examples.
2. Generate deterministic candidate units.
3. Ask Claude to rank/assemble using Style DNA and explicit project constraints.
4. Apply learned numeric distributions within safe bounds.
5. Render alternatives where uncertainty is material.
6. Record the exact Style DNA version and examples used.

## 12. Learning after every edit

After the user approves an export:

- align approved export to Coach's proposal;
- show a concise change summary;
- ask: **Should Coach learn from this finished version?**
- if yes, add it as a new candidate example;
- produce a proposed Style DNA version;
- show what would change;
- require approval.

Do not update after every intermediate export. Learn only from an explicitly approved final.

## 13. A/B preference acceleration

Where the dataset is small or inconsistent, show two previews differing in one dimension:

- tighter versus more relaxed pauses;
- faster versus calmer shot length;
- fewer versus more punch-ins;
- shorter versus longer captions;
- more versus less B-roll.

Record the choice and context. Never vary multiple dimensions at once in a learning comparison.

Also compare **Faithful** versus **Enhanced** edits. Enhanced may add clearly identified Coach ideas while preserving the learned editor fingerprint. Record idea type, context, acceptance, modification and removal so creative flair becomes personalised rather than random.

## 14. Data governance

- Keep dataset media at its existing local paths.
- Store hashes and derived analysis, not duplicate full-resolution footage.
- Do not commit dataset media to git.
- Provide per-example exclusion and verified **Finish & Free Space** cleanup.
- After learning, allow scripts, approved finals and compact learning capsules to remain while large raw files move to macOS Trash.
- Preserve parsed scripts, raw/final hashes and metadata, alignment/edit-decision features, representative low-resolution evidence, Style DNA contribution and provenance so the preference remains useful without the original 2 GB media.
- Never auto-delete, permanently delete or empty Trash. Show exact targets/count/size, require explicit confirmation and block media shared by another project hash. Never target CapCut cloud/account, Google Drive or a mounted/synchronised cloud folder; only Coach staging/caches and approved standalone local raw files are eligible.
- If a file disappears outside Coach, retain provenance but flag the example unavailable and never claim it can be re-aligned.
- Never send full training media to Claude by default.
- Obtain permission to use client/editor material for this personal learning workflow.

## 15. When the system should refuse to learn

- Final is not approved.
- Raw footage is materially incomplete and no readable project exists.
- Alignment confidence is too low.
- The video intentionally follows a one-off different style.
- The user marks it Do Not Copy.
- The example contains editing mistakes the user does not want repeated.
- Rights/permission are unclear.

## 16. Evaluation report

After initial learning, generate:

- examples imported/included/excluded;
- alignment coverage per example;
- extracted feature summary;
- conflicts and unknowns;
- held-out results;
- estimated confidence, not a fake accuracy percentage;
- recommended next examples that would add the most information.
