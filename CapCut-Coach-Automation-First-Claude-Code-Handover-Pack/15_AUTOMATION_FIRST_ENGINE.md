# Automation-First Editing and Rendering Engine

## 1. Product decision

CapCut Coach creates a near-finished video independently. CapCut Free is an optional finishing and inspection destination, not the primary renderer and not a runtime dependency for creating an MP4.

This is the key change that maximises automation when the owner has:

- no editor-authored CapCut projects;
- no initial finished examples;
- CapCut Free rather than Pro;
- script packs and large raw footage;
- a preference for one-click creation and later learning.

## 2. Default owner workflow

1. Press **Create video**.
2. Add a script pack, raw-footage folder and optional asset pack.
3. Coach parses, separates, analyses and matches everything automatically.
4. Coach creates **Clean**, **Enhanced** and **Bold** rendered previews.
5. The owner selects one or gives a simple change such as **stronger opening**, **faster**, **less text** or **different clip**.
6. Coach re-renders and produces the final MP4 itself.
7. Optionally press **Open in CapCut Free** for manual adjustments.
8. Approve the export; Coach learns from the choice and any replacement final.
9. Press **Free local space** for eligible local working files only.

Only the final creative approval and any destructive local cleanup are mandatory owner gates.

## 3. Render architecture

Use one typed, versioned `RenderGraph` as the source of truth for preview and final output.

```text
ProjectBrief
  -> ScriptPlan
  -> MediaCatalog
  -> EditPlan
  -> RenderGraph
  -> Preview MP4
  -> Final MP4
```

`RenderGraph` nodes include:

- source clip and in/out range;
- timeline start/duration;
- crop/reframe/scale/rotation;
- playback speed and optional ramp approximation;
- colour transform;
- opacity/transform keyframes;
- transition;
- text/graphic overlay;
- caption event;
- logo/CTA/end card;
- audio gain/fade/ducking;
- source and decision provenance.

Preview and final must compile from the same graph so approval is meaningful.

## 4. Zero-additional-cost renderer

Primary engine: FFmpeg/ffprobe with VideoToolbox where compatible.

Use:

- `trim`/`atrim`, `setpts`/`asetpts` and `concat` for assembly;
- `crop`, `scale`, `pad`, `transpose` and subject-aware coordinates for format;
- `xfade` for approved restrained transitions;
- `zoompan`, overlay expressions and generated keyframes for motion;
- `eq`, `curves`, `colorbalance`, `lut3d` and `colorspace` for looks;
- `loudnorm`, filters, fades, crossfades and sidechain compression for audio;
- ASS/libass for timed captions and kinetic emphasis;
- SVG/PNG template assets compiled locally for lower thirds, hooks, steps, logos, offer cards and CTA/end cards;
- VideoToolbox H.264/HEVC for fast Mac preview/final encoding, with a software fallback.

Build a small declarative motion-template library rather than a general compositor. Each template exposes safe parameters such as text, accent colour, entry/exit duration, position and intensity. Validate text fit before rendering.

## 5. Renderer licensing rule

Remotion must not be a required dependency. Its August 2026 licensing can charge for creator seats or automated rendering depending on the use case. The zero-extra-cost release uses FFmpeg plus locally generated ASS/SVG/raster assets.

Remotion is excluded from this edition because the owner requires zero additional spend. Do not scaffold, install or call it. The rejection is documented so a coding agent does not reintroduce it for convenience.

Sources:

- https://www.remotion.dev/docs/pricing
- https://www.remotion.dev/docs/license/faq

## 6. Automatic visual editing

For each requested script beat:

1. Build eligible clip/range candidates from local labels, scene boundaries, quality, composition and semantic match.
2. Enforce hard constraints: correct people/service, readable result, no unusable blur, no accidental exposure, correct orientation and rights.
3. Rank candidates for semantic fit, visual quality, novelty versus adjacent shots, learned taste and continuity.
4. Optimise the full sequence rather than greedily choosing each shot.
5. Add cutaways to conceal dialogue edits or create visual variety.
6. Keep one or two alternatives for every decision so replacement is instant.

The optimiser penalises repeated angles, repeated subjects, jumpy visual direction, excessive effects, unreadable text and mismatched claims.

## 7. Format playbooks

V1 supports:

### Scripted story/offer reel

Hook -> problem/context -> steps/proof -> result -> CTA.

### Treatment/service montage

Attention detail -> environment/equipment -> professional action -> close detail -> client/result -> brand end card.

### Talking/educational reel

Hook -> complete claims -> cut mistakes/restarts -> supporting B-roll -> captions -> CTA.

### Testimonial/interview

Best outcome quote -> context/problem -> experience/proof -> recommendation/CTA.

The universal taste profile is shared. Playbooks provide structural constraints, not separate brand models.

### Owner-supplied calibration evidence

Use the supplied videos and script pack as private evaluation references, not bundled fixtures:

- The 16.6-second vertical treatment montage demonstrates a visually led playbook: roughly eleven concise shots, treatment/environment/detail progression and a logo outro.
- The 23-second SmileBoxx reel demonstrates a scripted story playbook: immediate hook, five compact steps and a clear CTA in a 1080×1920 delivery.
- The campaign documents demonstrate structured inputs containing reels, numbered shots, spoken lines, time guidance, overlays, cutaways, transitions, pacing and end cards. The parser must preserve these fields while treating music notes as optional for this owner.

Create sanitised synthetic fixtures with the same structural properties for automated tests. Never commit or redistribute the owner's client media, scripts, transcripts or extracted frames.

## 8. Automation levels

- **Guide me** — approve script mapping and rough sequence before rendering.
- **Review first cut** — default; Coach completes analysis and renders candidates, then asks for one review.
- **Autopilot** — unlocked after five successful jobs; Coach chooses Enhanced, renders final and asks only for final approval.

Publishing/uploading remains outside scope unless separately authorised. Autopilot never bypasses factual review or local-deletion confirmation.

## 9. Free-first CapCut handoff

Coach detects installed CapCut version and current account capability without assuming Pro.

For CapCut Free:

- output a final MP4 usable without CapCut;
- output SRT and individual selected clips/assets when useful;
- provide a Free-compatible finishing guide;
- never recommend a locked asset without a clearly marked free alternative;
- optionally open a safe flattened final or prepared media folder in CapCut.

If Pro is later detected, additional templates/effects can be suggested, but the core renderer and final export remain independent.

## 10. Failure containment

- If Claude is unavailable, use deterministic script and playbook planning.
- If visual labelling is uncertain, render with conservative candidates or ask one thumbnail choice.
- If a transition/effect fails, fall back to a clean cut.
- If final rendering fails, retain the graph and resume the failed segment.
- If CapCut is unsupported/unavailable, final local rendering still works.

## 11. Automation-first release gates

- From raw + script only, generate three playable candidates without Terminal or CapCut.
- No reference videos or CapCut projects are required for onboarding.
- Preview/final frames match within defined encode tolerance.
- Every visual/script claim is traceable.
- Owner can replace a suggested clip in two clicks.
- Final MP4 passes black/freeze/audio/text-safe-area/QC checks.
- A first-time user completes the workflow with no more than one ambiguity question on the golden fixture.
