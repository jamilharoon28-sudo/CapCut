# Cost and Operating Budget

Research date: 4 August 2026. Re-check subscription policies before release.

## 1. Owner cost conclusion

For this one-user local application, mandatory additional cost is **$0 per month** beyond subscriptions/storage the owner already maintains. This is a hard owner requirement and release blocker, not a target.

The owner already has:

- Apple-silicon M2 Mac;
- CapCut Desktop Free, optionally installed;
- Claude Max 5x at $100/month;
- local or Google Drive media storage.

The product must not require hosting, a paid database, Redis, a SaaS account, cloud rendering, paid transcription or another AI subscription.

## 2. Build-time cost

Interactive Claude Code uses the owner's Max plan allocation. Max 5x is currently $100/month and provides five times the per-session capacity of Pro plus weekly limits. If usage credits/API billing are not enabled, reaching a limit pauses work rather than creating an extra bill.

Planning expectation:

- useful local vertical slice: approximately 1–2 focused weeks;
- robust three-format personal product: approximately 4–8 weeks including Mac/CapCut evidence testing.

This may span one or two subscription billing cycles, but the subscription is already owned. Do not promise completion within one usage window.

Sources:

- https://support.claude.com/en/articles/11049762-choose-a-claude-plan
- https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan

## 3. Runtime Claude budget

As of 15 June 2026, `claude -p` and Claude Agent SDK calls use a separate monthly allowance. Max 5x users can claim a $100 monthly Agent SDK credit. Interactive Claude Code remains under normal plan limits.

Runtime policy:

- local analysis does the heavy work;
- Claude receives structured script text, transcript/features and a few low-resolution frames;
- target one editorial planning call and, only when needed, one repair/creative call per candidate set;
- cache by content/config/prompt fingerprint;
- display monthly allowance status;
- paid overage, usage-credit auto-reload and API-key fallback are disabled by default;
- hard-stop automated Claude calls when the available allowance reaches the owner-set floor;
- local ingest, proxies, transcription, deterministic cutting, previews and QC continue without Claude.

The target is to keep approximately 40 short videos/month inside the included Agent SDK credit, but this is a benchmark target—not a guarantee. Record actual per-project allowance consumption during the first ten videos and adjust call frequency/model/context.

Source: https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan

## 4. Google Drive cost

Google Drive for desktop uses the owner's existing storage plan. Stream mode keeps most data in the cloud and downloads content when accessed; Mirror mode keeps a full local copy and should not be recommended for this workflow.

Standard Google Drive API use is currently available at no additional cost under the documented threshold. The product's single-user volume is expected to remain far below the current 1 TB/day egress threshold. Google states future over-threshold charges are planned, so the doctor must display the current policy link and never assume it is permanent.

Sources:

- https://support.google.com/drive/answer/13401938
- https://developers.google.com/workspace/drive/api/guides/limits

## 5. Open-source/local components

Expected additional monetary cost: $0.

- FFmpeg/ffprobe;
- whisper.cpp models;
- PySceneDetect;
- SQLite;
- FastAPI;
- React/TypeScript;
- local macOS helper;
- optional compatible CapCut adapter, not used by the primary renderer.

Licensing and redistribution obligations still apply even when software is free.

## 6. Excluded paid options

- No CapCut Pro requirement.
- No Remotion seat/automation licence.
- No Claude usage credits, auto-reload or paid API fallback.
- No hosted database, storage, render worker or analytics.
- No paid transcription/vision API.
- No Apple Developer membership for personal local v1.

If existing Drive storage becomes insufficient, the application stops importing rather than recommending an automatic purchase. External storage remains a personal hardware choice outside the application, not a product dependency.

## 7. Cost acceptance gates

- Fresh install asks for no payment method.
- With overage disabled, a limit produces a clear pause/fallback, not a charge.
- Cost screen separates existing subscriptions, included allowances, estimated project consumption and actual additional spend.
- Default additional-spend ceiling is exactly $0.
- Dependency and network tests fail if a paid/licence-gated service is required for a normal project.
- No third-party telemetry, hosted analytics or surprise storage service.
