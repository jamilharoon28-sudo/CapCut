# M2 Benchmark Record (P0.5)

Run `python3 scripts/benchmark.py --input <10min-1080p.mov>` on the owner's Mac.
The harness measures each stage independently and picks Quiet / Balanced /
Maximum defaults from evidence. **Not yet run** — this scaffold is on Linux CI.

Record for every run: exact Mac model, RAM, macOS, power state, tool versions,
and input properties (codec, fps, VFR, resolution, duration).

| Stage | Wall time | Peak memory | Output size | CapCut still usable? |
| --- | --- | --- | --- | --- |
| 720p proxy (VideoToolbox) | ⛔ | ⛔ | ⛔ | ⛔ |
| Audio extract (mono 16 kHz) | ⛔ | ⛔ | ⛔ | ⛔ |
| whisper.cpp (candidate models) | ⛔ | ⛔ | ⛔ | ⛔ |
| Preview render | ⛔ | ⛔ | ⛔ | ⛔ |

## Chosen defaults

- Quiet / Balanced / Maximum thresholds: _pending evidence_.
- Selected whisper model: `auto-benchmarked` (config default) → _pending_.

No hard thermal-limit claim is made. Protection relies on one-job-at-a-time, low
process priority, proxies, caching, and macOS scheduling; measured behaviour is
displayed rather than asserted.
