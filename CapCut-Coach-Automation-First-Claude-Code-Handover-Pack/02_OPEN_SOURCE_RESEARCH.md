# Open-Source and Platform Research

Research date: 4 August 2026. Re-check upstream status and licenses at implementation time; CapCut and repository behaviour can change without notice.

## 1. Research conclusion

No single repository safely delivers the requested Mac application. The correct approach is a controlled composition:

- use `capcut-cli` as the first CapCut inspection/write candidate because it has explicit Mac draft-layout support, diagnostics, linting, backups and version guards;
- use `whisper.cpp`, FFmpeg and PySceneDetect for local deterministic processing;
- reuse the silence/repetition concepts from SmartCut and the proven preprocessing approach of Auto-Editor;
- implement our own paired raw/final alignment, Style DNA, beginner UX, CapCut compatibility registry, safety transaction and QC;
- treat feature-rich JianYing/CapCut API repositories as research or optional adapters until they pass Mac fixtures and license checks;
- never trust README feature claims without a canary-project test on the user's exact CapCut build.

## 2. Primary repository shortlist

### 2.1 renezander030/capcut-cli — recommended CapCut core

Repository: https://github.com/renezander030/capcut-cli  
License: MIT  
Observed status: active; v0.16 documentation visible during research  

Useful capabilities:

- local JSON-in/JSON-out CLI and typed library;
- inspect and edit CapCut/JianYing projects;
- captions, timing, speed, volume, filters, effects and templates;
- long-form cutting and timeline export;
- newer Mac `draft_info.json`-primary layout support;
- detection/synchronisation of multiple readable timeline mirrors;
- version diagnostics, linting, backups and write guards;
- refusal on unsupported/beyond-evidence draft generations unless a user explicitly forces a write.

Use it for:

- Phase 0 project diagnostics;
- read-only timeline/caption/media inspection;
- adapter primitives after the exact version passes canary tests;
- fixture creation and redacted support bundles;
- linting and validation;
- OpenTimelineIO export where useful.

Do not:

- automatically use `--force-write`;
- assume its expected-compatible rows have been tested in the user's desktop app;
- modify the user's original project;
- run mutations while CapCut is open.

Compatibility warning: its published matrix reports CapCut 10.x on Mac/Windows as write-guarded because externally written drafts have been reported as corrupt. The pack therefore makes direct writes conditional on the exact version/schema canary.  
Matrix: https://github.com/renezander030/capcut-cli/blob/master/docs/version-support.md

### 2.2 mrbuslov/capcut-ai-editor (SmartCut) — dialogue-editing reference

Repository: https://github.com/mrbuslov/capcut-ai-editor  
License: MIT  

Useful capabilities:

- reads CapCut auto-generated captions;
- removes silence based on caption gaps;
- detects repeated takes and keeps the later attempt;
- exposes an MCP server suitable for Claude-assisted calls;
- targets talking-head editing.

Important limitations:

- its README says smart cut modifies a project in place and does not create a backup;
- it requires CapCut-generated captions before processing;
- simple gap thresholds can create unnatural cuts;
- it is not a full preference-learning or finishing system.

Use it for:

- tests and algorithm ideas for duplicate-take detection;
- transcript-derived silence candidates;
- comparison fixtures.

Do not adopt its in-place mutation behaviour. All Coach mutations must use the transaction in the master spec.

### 2.3 WyattBlue/auto-editor — mature preprocessing reference

Repository: https://github.com/WyattBlue/auto-editor  
License: Unlicense/public-domain dedication for repository source; verify binary notices separately  

Useful capabilities:

- automatic editing based on audio loudness and motion;
- configurable margins around active speech;
- multiple label/actions system;
- exports to Premiere, Resolve, Final Cut Pro, Shotcut, Kdenlive and clip sequences;
- mature command-line behaviour and substantial history.

Use it for:

- benchmarking silence/motion detection;
- margin semantics and previewing what will be cut;
- possible library/subprocess use if the lockfile and license review are clean.

Do not treat loudness alone as an editorial decision. Coach must preserve phonemes, breath and semantic completeness.

### 2.4 ggml-org/whisper.cpp — recommended local transcription

Repository: https://github.com/ggml-org/whisper.cpp  
License: MIT  
Observed stable release during research: v1.9.1  

Why selected:

- Apple Silicon is explicitly treated as a first-class platform;
- supports ARM NEON, Accelerate, Metal and Core ML;
- local/offline operation;
- quantised models and voice activity detection;
- simple CLI and C API;
- appropriate for an M2 without a Python GPU stack.

Implementation notes:

- benchmark at least two model sizes on the actual Mac;
- store model hash/version with transcript cache metadata;
- use word timestamps and VAD;
- do not redistribute optional examples with incompatible licenses without review;
- use an application-managed model directory and verify checksums.

### 2.5 FFmpeg/ffprobe — required media engine

Repository: https://github.com/FFmpeg/FFmpeg  
License: mainly LGPL 2.1+; enabling certain optional components changes the build to GPL 2+  

Use it for:

- probing media;
- proxy and preview generation;
- audio extraction;
- loudness analysis/normalisation;
- hardware encoding through VideoToolbox where available;
- scene/black/freeze/silence checks;
- crop/scale/overlay/subtitle preview rendering;
- thumbnails, contact sheets and waveforms.

Licensing rule:

- during personal development, Homebrew/system FFmpeg is acceptable;
- if a binary is later bundled, record its exact configuration and comply with LGPL/GPL obligations;
- avoid `--enable-nonfree` builds;
- keep FFmpeg as a separate executable, not copied source.

Official license: https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md

### 2.6 Breakthrough/PySceneDetect — selected shot-boundary engine

Repository: https://github.com/Breakthrough/PySceneDetect  
License: BSD 3-Clause  

Useful capabilities:

- content, adaptive, hash, histogram and threshold detectors;
- scene/shot timecode output;
- statistics export;
- EDL and OTIO output;
- automatic image and split-video support.

Use it for:

- final-video cut boundary detection;
- raw/final alignment segmentation;
- pacing feature extraction;
- contact sheets and scene statistics.

Limitation: its “scene” detection is primarily visual shot-boundary detection; semantic scene understanding remains Coach's responsibility.

### 2.7 OpenTimelineIO — internal interchange option

Repository: https://github.com/AcademySoftwareFoundation/OpenTimelineIO  
License: modified Apache 2.0 / project notices; verify current files  

Use it for:

- optional interchange/export;
- a debug representation of the internal edit plan;
- future Final Cut/Resolve handoff.

Do not make the core domain model dependent on CapCut JSON or OTIO. Maintain a small typed internal schema and write adapters.

## 3. Secondary repositories and decisions

### Hommy-master/capcut-mate

Repository: https://github.com/Hommy-master/capcut-mate  
License: Apache 2.0  
Observed scale: hundreds of commits; FastAPI-based  

Claims draft, media, captions, effects, masks, keyframes and cloud rendering. It is primarily described as a JianYing assistant and includes China-specific Coze/cloud workflows. Evaluate individual modules and tests, but do not make it the Mac runtime foundation without a real CapCut International fixture test.

Decision: **research/optional module only**.

### ashreo/CapCutAPI

Repository: https://github.com/ashreo/CapCutAPI  

Claims cross-platform CapCut/JianYing support, REST and MCP, multi-track editing, keyframes, effects and subtitles. Feature claims are broad. Before using any source:

1. verify the repository's current license file;
2. inspect tests and fixture evidence;
3. run only against a disposable project;
4. compare its schema handling to the safety and version evidence in `capcut-cli`.

Decision: **evaluate after Phase 0; do not trust as “enterprise-grade” merely because the README says so**.

### GuanYixuan/pyCapCut

Repository: https://github.com/GuanYixuan/pyCapCut  
Observed scale during research: 18 commits and approximately 625 stars  

Attractive capabilities include template duplication, media replacement, tracks, keyframes, masks, animations, filters, transitions and SRT styling. However:

- the project says migration from pyJianYingDraft is still in progress;
- several modules are marked experimental/newly migrated;
- its documentation says macOS can install/use it, but generated drafts still require Windows CapCut for export;
- no clear license was visible in the repository root during research.

Decision: **do not copy or vendor code unless a compatible license is confirmed; use as behavioural research only. Not the M2 foundation.**

### GuanYixuan/pyJianYingDraft

Repository: https://github.com/GuanYixuan/pyJianYingDraft  
License: Apache 2.0  
Observed scale: approximately 4.1k stars  

Feature-rich, but it targets JianYing. JianYing 6+ encrypted draft formats are a separate compatibility and legal risk. The user runs CapCut International, so this is not the production adapter.

Decision: **reference for concepts/tests only**.

### Atx-Guy/capcut-mcp-server

Repository: https://github.com/Atx-Guy/capcut-mcp-server  
Observed status: one commit during research; wrapper requires VectCutAPI  

Decision: **reject as foundation**. It adds an MCP surface but does not solve compatibility, safety, local Mac export or preference learning.

### sun-guannan/VectCutAPI

Repository: https://github.com/sun-guannan/VectCutAPI  

Agent-oriented editing API with draft export and a Claude skill. It may offer ideas for tool schemas, but it is cloud/API-oriented and must pass license, local-deployment, privacy and Mac fixture tests.

Decision: **research only unless Phase 0 evidence changes the decision**.

### emosheeep/capcut-export

Repository: https://github.com/emosheeep/capcut-export  

The maintainer declared end-of-life after newer draft encryption/schema changes affected it.

Decision: **do not use**. It is useful only as historical evidence that CapCut/JianYing project compatibility can break abruptly.

### vogelcodes/capcut-srt-export

Repository: https://github.com/vogelcodes/capcut-srt-export  

Small utility that documents a common Mac project location and extracts captions from CapCut project JSON.

Decision: **reference only**. `capcut-cli` provides broader, safer inspection.

### CapCut subtitle converters with minimal activity

Repositories such as `naruepanart/capcut-subtitle-json-to-srt` duplicate narrow extraction functionality and showed very low activity during research.

Decision: **not required**.

## 4. Repositories that may help later

These are optional and must not enlarge the first build unnecessarily.

### snakers4/silero-vad

Repository: https://github.com/snakers4/silero-vad  
Potential use: local voice activity detection if whisper.cpp VAD is insufficient.

### facebookresearch/demucs

Repository: https://github.com/facebookresearch/demucs  
Potential use: separate voice from music in finished examples to improve raw/final audio alignment. It is heavy; defer until alignment tests prove it necessary.

### librosa/librosa

Repository: https://github.com/librosa/librosa  
Potential use: MFCC, chroma, beat and audio feature extraction for alignment and music analysis.

### opencv/opencv

Repository: https://github.com/opencv/opencv  
Potential use: frame matching, perceptual comparison, optical flow and crop/zoom inference.

### asweigart/pyautogui or Hammerspoon

Potential use: rapid UI-automation prototype. Production macOS control should use AXUIElement through the Swift bridge before coordinate-based automation.

### remotion-dev/remotion

Repository: https://github.com/remotion-dev/remotion  
Current decision: **reject for the required workflow**. Its August 2026 licensing can require a paid creator seat or automation licence. The owner's requirement is zero additional spend. Use FFmpeg plus local ASS/SVG/raster templates instead. Reconsider only if the owner later explicitly changes the cost rule.

## 5. Official CapCut facts used in the design

### External subtitle import

CapCut's official help says CapCut Desktop on Windows/macOS can import UTF-8 `.srt` or timecoded `.txt` through **Captions → Add Captions**, generating editable synchronized text blocks. This is the guaranteed fallback path.  
Source: https://www.capcut.com/help/how-to-import-subtitles

### Auto captions

CapCut Desktop supports Auto Captions and manual timing/text/style adjustments. Coach should not depend on CapCut transcription because local word timestamps are required, but it may compare results.  
Source: https://www.capcut.com/help/how-to-recognise-subtitles

### Batch caption behaviour

CapCut supports batch caption editing, but imported/manual and auto-generated caption groups can behave differently with “Apply to all.” Guided Mode must account for this and validate a test segment.  
Source: https://www.capcut.com/help/fix-apply-to-all-captions-error

### No official desktop project API found

The research found official guides for imports, captions and editing, but no supported public desktop project-write API. Direct draft editing therefore remains unofficial and version-gated.

## 6. Official macOS integration facts

- Apple's FSEvents API notifies applications about changes inside directory hierarchies. It is appropriate for project/export watching.  
  https://developer.apple.com/documentation/coreservices/file_system_events
- AXUIElement exposes accessible UI objects and actions and is the correct basis for assistive control of macOS applications.  
  https://developer.apple.com/documentation/applicationservices/axuielement
- AXUIElement functions allow assistive applications to communicate with and control accessible macOS applications. Accessibility permission is therefore required for optional Guided Mode automation.  
  https://developer.apple.com/documentation/applicationservices/axuielement_h

## 7. Claude Code and Agent SDK facts

- Claude's Agent SDK is available in Python and TypeScript; another language can invoke the CLI with `-p` and `--output-format json`.  
  https://docs.anthropic.com/en/docs/claude-code/sdk
- The $100 plan is Max 5x, which provides five times the per-session capacity of Pro plus weekly limits. Exact prompts/tokens are not a fixed published bucket.  
  https://support.claude.com/en/articles/11049741-what-is-the-max-plan
- Interactive Claude Code and Claude chat share normal subscription limits.  
  https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan
- As of 15 June 2026, Agent SDK and `claude -p` usage use a separate monthly allowance; Max 5x users can claim a $100 monthly Agent SDK credit. Re-check this policy before implementation.  
  https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan
- Anthropic recommends clearing context between distinct tasks because conversation history and project context are resent and consume usage.  
  https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code

## 8. License and supply-chain rules

Before the first release:

1. Generate `THIRD_PARTY_NOTICES.md` from the exact locked dependency graph.
2. Record repository URL, revision/package version, license and how it is used.
3. Do not copy code from repositories without an explicit compatible license.
4. Prefer subprocess invocation over vendoring large upstream codebases.
5. Pin versions and verify checksums for downloaded binaries/models.
6. Run dependency vulnerability and license scans.
7. Never run arbitrary install scripts from unreviewed repositories.
8. Do not bundle FFmpeg until the chosen build's LGPL/GPL configuration is documented.
9. Keep modifications to third-party source isolated and preserve notices.
10. Re-check licenses if the application is ever distributed beyond the owner.

## 9. Upstream intake checklist

For any additional GitHub repository, Claude Code must answer:

- What exact missing capability does it provide?
- Is it more reliable than implementing the small capability locally?
- What is the license?
- Is there a test suite?
- Are real CapCut International Mac fixtures present?
- When was it last meaningfully maintained?
- Does it write drafts atomically and make backups?
- Does it detect CapCut versions and canonical timeline files?
- Does it work when CapCut is closed only?
- Can it be pinned reproducibly?
- Does it upload media or call unknown services?

If these answers are unclear, do not add the dependency to the critical path.
