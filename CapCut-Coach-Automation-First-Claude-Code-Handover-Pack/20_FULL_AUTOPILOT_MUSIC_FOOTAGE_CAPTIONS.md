# Full Autopilot — Music, Footage and Captions

## 1. Product outcome

Coach performs the complete first edit automatically from script and raw footage:

- understands the script and desired outcome;
- finds and ranks usable footage ranges;
- builds the visual story;
- selects an eligible soundtrack from an approved library;
- edits on meaningful audio phrases/onsets;
- transcribes speech and creates styled captions;
- creates campaign text, graphics and branded outro;
- cleans/mixes audio;
- renders the final MP4 and runs QC;
- asks only for final approval or a genuinely blocking ambiguity.

The owner-facing primary action is **Make My Video**. Technical stages remain visible as calm progress, not configuration.

## 2. Automatic footage editor

For every raw asset/range, derive locally:

- transcript and word timestamps;
- scene/action boundaries;
- subject/face/object/product/equipment labels;
- OCR and filenames/folder context;
- orientation, framing and crop safety;
- blur, exposure, shake, obstruction and audio quality;
- shot size, motion, novelty and similarity to other ranges;
- script/visual-role match and confidence.

Cluster repeats and alternate takes. For each script beat, keep the best eligible range plus two backups. Optimise the whole sequence for meaning, role coverage, visual variety, continuity, pacing and Audio DNA—not clip by clip in isolation.

Hard rules:

- no footage may imply a claim/result it does not show;
- avoid accidental adjacent duplicates and repeated angles;
- preserve the best visible part of each action;
- never cut outside the source or hide uncertainty;
- keep alternatives so **Change this clip** is instant;
- missing required footage routes to Smart Preflight with recording guidance.

## 3. Automatic approved-music library

### Sources

Coach may automatically choose only from:

- an owner-selected local **Approved Music** folder;
- an owner-selected read-only Google Drive music folder staged locally;
- tracks shipped with the application only when redistribution/usage rights are documented.

Never rip, record, extract or download music from Spotify, YouTube, TikTok, Instagram, CapCut, a finished reference or an unapproved website. A reference track may contribute derived tempo/energy preferences only.

### Music record

```json
{
  "id": "music_uuid",
  "content_hash": "sha256",
  "path_ref": "security_scoped_bookmark",
  "title": "Owner label",
  "rights_status": "OWNER_APPROVED",
  "rights_note": "Local licence/receipt/reference",
  "allowed_uses": ["organic_social"],
  "expires_at": null,
  "bpm": 120.2,
  "duration_s": 92.4,
  "energy": 0.66,
  "mood_tags": ["warm", "uplifting", "premium"],
  "vocals": false,
  "sections": [],
  "analysis_version": "audio_dna_v1"
}
```

### Selection

Score eligible tracks using:

- script mood, objective and audience;
- learned owner/editor preferences;
- format playbook and desired pacing;
- duration and usable musical ending;
- tempo/phrase suitability;
- energy arc;
- vocal conflict with dialogue;
- brand restrictions and documented usage rights.

Choose the highest safe score and store the next two alternatives. Explain the choice under **Why Coach chose this**. The owner can tap **Try different music** without rebuilding footage analysis.

### Editing and mixing

- Fit the edit to musical phrases, not every beat.
- Cut/restructure the track only on compatible phrase/bar boundaries.
- Prefer an authentic ending; otherwise use a controlled fade.
- Do not heavily time-stretch. A small configurable change may be used only when it does not create audible artefacts.
- Dialogue leads. Duck music automatically using speech activity and restore it smoothly.
- Use equal-power fades/crossfades and avoid clicks.
- Use local approved SFX sparingly and never to disguise a weak edit.
- Begin social testing around -14 LUFS integrated and <= -1 dB true peak, then learn the approved range.

If no eligible music exists, Smart Preflight offers: **Choose an Approved Music folder**, **Upload one track**, or **Continue without music**. It does not block when a strong speech/silent edit is viable.

## 4. Automatic captions and campaign text

### Speech captions

- Use whisper.cpp word timestamps plus VAD locally.
- Apply approved vocabulary for people, brands, treatments and locations.
- Restore punctuation/casing without changing spoken meaning.
- Break captions by phrase and meaning, not fixed character count alone.
- Enforce phone-readable line length, duration, safe zones and no overlaps.
- Highlight active words only where consistent with Style DNA.
- Avoid covering faces, products, treatment details or CTA graphics.
- Export both styled burn-in captions and UTF-8 SRT unless the project requests otherwise.
- Flag low-confidence names, prices, dates and claims for one grouped factual review.

### Script-led on-screen text

When there is no speech, Coach creates campaign text beats from the script, as in the Mothers' Day target. These are not transcripts. They must form a coherent hook/body/CTA story, preserve facts and use the brand pack's typography/emphasis rules.

Never invent an offer, result, price, date, medical claim, contact detail or testimonial. Route missing facts to Smart Preflight.

## 5. Full Autopilot modes

- **Review candidates** — Coach renders Clean/Enhanced/Bold; owner chooses.
- **Make My Video** — available from day one; Coach selects its best safe candidate and renders the final for approval.
- **Trusted Autopilot** — after five safe approved jobs in that format; Coach also applies low-risk learned preferences with fewer interruptions.

All modes require final owner approval before publishing. Publishing and destructive cleanup remain separate explicit actions.

## 6. Automatic final selection

Score candidate RenderGraphs on:

- complete script/fact coverage;
- visual-role coverage and source quality;
- story clarity and hook strength;
- caption/text readability;
- Audio DNA alignment and mix safety;
- brand/CTA completion;
- learned preference fit;
- repetition/effect penalties;
- factual/safety uncertainty;
- technical QC.

Render the highest safe candidate. Keep the other graphs available but do not waste storage rendering all full-resolution versions unless requested.

## 7. One-screen beginner experience

Home shows **Make My Video**. The project screen shows:

1. **Checking what you gave me**
2. **Understanding the script and footage**
3. **Choosing shots, music and captions**
4. **Building your video**
5. **Checking the final**
6. **Ready to watch**

If input is needed, show one grouped Smart Preflight card. Normal mode never exposes BPM, embeddings, VAD, codecs, command lines or model names.

Final review offers only:

- **Approve**
- **Change a clip**
- **Try different music**
- **Fix caption/text**
- **Faster / calmer**
- **Try another version**

## 8. Performance and storage

- Index raw footage and music once by content hash.
- Analyse proxies/PCM incrementally; never load a multi-gigabyte video into memory.
- Run one heavy stage at a time on the M2.
- Re-render only changed segments where technically safe.
- Use preview resolution for selection and hardware encoding for final where validated.
- Music indexes and caption models live in the cache budget and remain removable/rebuildable.

## 9. Acceptance gates

### Complete no-edit workflow

- From script + raw folder + approved music library + optional brand pack, **Make My Video** produces a valid final MP4 without manual timeline editing, CapCut or paid services.
- The owner encounters no more than one grouped non-safety interruption before review on a complete golden fixture.

### Footage

- Every selected range is traceable to a valid source and required story beat.
- The sanitised Mothers' Day fixture passes visual-role, narrative, pacing and branded-outro requirements.
- Removing one required shot produces accurate Smart Preflight recording guidance rather than fabrication.

### Music

- Only rights-eligible indexed tracks can be selected.
- Selection is reproducible from documented scores and offers two eligible alternatives.
- At least 85% of montage cuts land within the permitted onset/phrase window without violating semantic/action constraints.
- Dialogue remains intelligible; the mix passes loudness, true-peak, silence and discontinuity QC.
- Tests prove no network/music-ripping code path is reachable from normal use.

### Captions/text

- Word/caption timestamps are monotonic, inside duration and non-overlapping.
- Names/prices/dates/claims below confidence threshold are grouped for review.
- Captions stay inside safe zones and avoid protected visual regions on golden fixtures.
- SRT and burn-in content agree after approved corrections.
- Script-led campaign copy preserves mandatory meaning and never invents facts.

### Cost and autonomy

- Required runtime cost remains $0 beyond existing subscriptions/storage.
- Claude unavailable/limited: deterministic footage, music, captions, render and QC still work; only optional semantic flair may degrade/pause.
- Final approval, publishing, new claims and cleanup are never silently automated.
