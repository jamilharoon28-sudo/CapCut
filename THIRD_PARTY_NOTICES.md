# Third-Party Notices

This file catalogues third-party components per `04_CLAUDE_CODE_RUNBOOK.md §10`.
Versions are pinned in `apps/backend/pyproject.toml` and
`apps/frontend/package.json`. Confirm current licenses before upgrading; do not
copy source from a repository without an explicit compatible license.

> **Note.** Exact versions must be re-pinned when dependencies are first
> installed on the target Mac (this scaffold was prepared offline). No
> third-party *source code* has been copied into this repository — only declared
> package dependencies and invoked binaries.

## Runtime binaries (invoked as subprocesses, not linked)

| Component | Purpose | License | Network | Handles user data |
| --- | --- | --- | --- | --- |
| FFmpeg / ffprobe | proxy, audio extract, probe | LGPL/GPL (build-dependent) | none | yes (local media only) |
| whisper.cpp | local transcription | MIT | none (models downloaded once, checksummed) | yes (local audio only) |
| Claude Code CLI (`claude`) | editorial decision provider | Anthropic ToS | yes (text + low-res frames only) | limited, opt-in |

## Python (backend)

| Package | Purpose | License |
| --- | --- | --- |
| fastapi | local HTTP API | MIT |
| uvicorn | ASGI server (loopback) | BSD-3-Clause |
| pydantic | typed models / validation | MIT |
| jsonschema | Claude output validation | MIT |
| python-multipart | form parsing (local only) | Apache-2.0 |
| pytest | tests | MIT |

Optional / lazy-imported (feature-gated, not required to start):
`python-docx` (MIT), `pypdf` (BSD), `scenedetect` (BSD-3-Clause),
`numpy` (BSD-3-Clause), `opencv-python-headless` (Apache-2.0 — footage analysis:
best-moment + subject reframe via bundled Haar cascades; no network, no model
download). Each is imported only when its feature runs, so the app starts and
passes core tests without them.

## Human Judgement Engine — planned components (ADR-0007/0008)

Licence register for components the layered engine will use. **None are vendored
or added as dependencies yet** — recorded here so each is a deliberate, licence-
checked decision before Phase 1–8 code imports it. Level A must run without any
Level-B/C component; each is feature-gated with a deterministic fallback.

| Component | Role | License | Network | Notes |
| --- | --- | --- | --- | --- |
| PySceneDetect (`scenedetect`) | shot boundaries | BSD-3-Clause | none | already optional-listed |
| OpenCV (`opencv-python-headless`) | blur/motion/duplicate verify | Apache-2.0 | none | already used (Haar) |
| Apple Vision (native) | face-capture quality, saliency, feature-prints, OCR | Apple system framework | none | via a sandboxed Swift CLI helper; JSONL over stdin/stdout, path-restricted |
| whisper.cpp | transcription | MIT | none (models checksummed) | already used |
| librosa | beat/tempo/onset | ISC | none | already used |
| Silero VAD | speech/no-speech (optional) | MIT | none | ONNX path preferred (avoid full PyTorch) |
| MLX | Apple-Silicon runtime (Level B) | MIT | none | optional |
| MLX-VLM | local VLM inference (Level B) | MIT | none | optional |
| Qwen3-VL 2B Instruct (4-bit MLX) | window description/critique (Level B) | Apache-2.0 (model) | none | pinned + checksummed conversion; ~1.8 GB, install/remove UI |
| OpenTimelineIO | timeline interchange/export only | Apache-2.0 | none | not a renderer; RenderGraph stays source of truth |
| TransNetV2 | harder transition detection (later, optional) | MIT | none | only if it beats PySceneDetect on the fixtures |

Deliberately **excluded** for v1: YOLO/Ultralytics (AGPL — redistribution
obligations need a separate decision; Apple Vision + OpenCV cover the first
release), VMAF (reference-based — cannot judge an unrelated raw shot), IQA-PyTorch
and VideoScore/VisionReward-style reward models (heavy PyTorch, aimed at
generated-video evaluation, not a default local editing dependency).

## JavaScript (frontend)

| Package | Purpose | License |
| --- | --- | --- |
| react / react-dom | UI | MIT |
| vite | dev server / bundler | MIT |
| typescript | types | Apache-2.0 |
| vitest | tests | MIT |
| @playwright/test | visual regression | Apache-2.0 |

## Swift (mac-bridge)

Uses only Apple system frameworks (AppKit, ApplicationServices/Accessibility,
UserNotifications). No third-party Swift packages.

## Dependency policy

Reject packages that duplicate small standard-library functionality, add a
server for a one-user local task, or have unclear licensing. For every
dependency record: exact version, license, why required, whether it handles user
data, whether it makes network calls, binary source/checksum, upgrade procedure,
and fallback/removal strategy (tracked in `docs/adr/` when material).
