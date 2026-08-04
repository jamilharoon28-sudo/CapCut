# Scripts

Stable command wrappers (runbook §4). All quote paths and support spaces.

| Script | Purpose | Platform |
| --- | --- | --- |
| `bootstrap.command` | one-time setup (uv, backend venv, pnpm deps, doctor) | macOS / Linux |
| `doctor.sh` | environment + CapCut + M2 probe (Mac checks blocked off-Mac) | any |
| `run-dev.sh` | run backend (loopback) + frontend dev server | any |
| `test.sh` | ruff + backend pytest (+ frontend tests when installed) | any |
| `benchmark.py` | M2 stage benchmark (needs FFmpeg / whisper.cpp) | any |
| `install-launchagent.sh` | start the local service at login | macOS |
| `uninstall-launchagent.sh` | remove the launchd agent | macOS |
| `backup-database.sh` | online SQLite backup outside CapCut's dirs | any |
| `restore-project.sh <id>` | locate a Coach backup; restore verified in-app | any |

## Running the backend tests in CI (Linux)

```bash
cd apps/backend
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[dev,scripts]"
ruff check capcut_coach && python -m pytest -q
```

Mac/CapCut/dataset-dependent steps are intentionally **blocked** off the target
Mac — see `docs/phase-evidence/`.
