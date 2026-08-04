"""ClaudeDecisionProvider — constrained, cached, non-executing (Phase 4).

Contract:
- Claude receives only pre-validated ids, transcript units, numeric features and
  (optionally) references to selected low-resolution frames — never raw video,
  never file paths it can act on.
- Every response is validated against a JSON Schema *and* semantically checked:
  unknown ids and out-of-range values are rejected (test F8). One schema-repair
  retry is allowed, then the deterministic fallback is used.
- Results are cached by (input + model + prompt version), so identical requests
  make no repeated calls.
- An allowance guard hard-stops before any paid overage (test S8); overage stays
  off unless the user explicitly enables it.
- The provider never executes model-generated commands or paths.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from jsonschema import Draft202012Validator

from .schemas import PROMPT_VERSION, SCHEMAS_BY_NAME


class ClaudeUnavailable(RuntimeError):
    pass


class AllowanceExceeded(RuntimeError):
    """Raised when a call would exceed the free allowance and overage is off."""


@dataclass
class DecisionResult:
    schema_name: str
    data: dict[str, Any]
    source: str  # "claude" | "cache" | "fallback"
    repaired: bool = False


class DecisionCache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put(self, key: str, schema_name: str, data: dict[str, Any]) -> None: ...


class InMemoryDecisionCache:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    def put(self, key: str, schema_name: str, data: dict[str, Any]) -> None:
        self._store[key] = data


@dataclass
class AllowanceMeter:
    """Tracks decision calls against a per-window budget; hard-stops overage."""

    limit: int
    used: int = 0
    overage_enabled: bool = False

    def check_and_reserve(self) -> None:
        if self.used >= self.limit and not self.overage_enabled:
            raise AllowanceExceeded(
                "Claude free allowance reached. Additional paid usage is off by default."
            )
        self.used += 1


def _input_key(schema_name: str, model: str, payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{schema_name}|{model}|{PROMPT_VERSION}|{blob}".encode()).hexdigest()
    return digest


def _collect_ids(payload: dict[str, Any], keys: tuple[str, ...]) -> set[str]:
    ids: set[str] = set()
    for key in keys:
        for item in payload.get(key, []) or []:
            if isinstance(item, dict) and "id" in item:
                ids.add(str(item["id"]))
            elif isinstance(item, str):
                ids.add(item)
    return ids


def _semantic_check(schema_name: str, data: dict[str, Any], allowed_ids: set[str]) -> list[str]:
    """Reject unknown ids / invalid ranges beyond structural JSON Schema (F8)."""
    errors: list[str] = []
    if schema_name == "hook_ranking":
        for r in data.get("ranking", []):
            if r["candidate_id"] not in allowed_ids:
                errors.append(f"unknown candidate id {r['candidate_id']}")
    elif schema_name == "narrative_plan":
        seen = set()
        for uid in data.get("ordered_unit_ids", []):
            if uid not in allowed_ids:
                errors.append(f"unknown unit id {uid}")
            if uid in seen:
                errors.append(f"duplicate unit id {uid}")
            seen.add(uid)
        for role in data.get("roles", []):
            if role["unit_id"] not in allowed_ids:
                errors.append(f"unknown unit id in roles {role['unit_id']}")
    return errors


class ClaudeDecisionProvider:
    """Base class wiring validation, caching, allowance and fallback together."""

    def __init__(
        self,
        *,
        model: str = "claude",
        cache: DecisionCache | None = None,
        allowance: AllowanceMeter | None = None,
        enabled: bool = True,
    ) -> None:
        self.model = model
        self.cache = cache or InMemoryDecisionCache()
        self.allowance = allowance or AllowanceMeter(limit=10_000)
        self.enabled = enabled

    # Subclasses implement the raw call. Base is deterministic-only.
    def _raw_call(self, schema_name: str, payload: dict[str, Any]) -> str:  # pragma: no cover
        raise ClaudeUnavailable("no Claude backend configured")

    def decide(
        self,
        schema_name: str,
        payload: dict[str, Any],
        *,
        allowed_id_keys: tuple[str, ...] = ("candidates", "units"),
        fallback: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> DecisionResult:
        if schema_name not in SCHEMAS_BY_NAME:
            raise ValueError(f"unknown schema {schema_name}")
        validator = Draft202012Validator(SCHEMAS_BY_NAME[schema_name])
        allowed_ids = _collect_ids(payload, allowed_id_keys)

        key = _input_key(schema_name, self.model, payload)
        cached = self.cache.get(key)
        if cached is not None:
            return DecisionResult(schema_name, cached, source="cache")

        if not self.enabled:
            data = fallback(payload)
            return DecisionResult(schema_name, data, source="fallback")

        repaired = False
        for attempt in range(2):  # original + one repair retry
            try:
                self.allowance.check_and_reserve()
                raw = self._raw_call(schema_name, payload)
                data = json.loads(raw)
                structural = sorted(validator.iter_errors(data), key=lambda e: e.path)
                semantic = _semantic_check(schema_name, data, allowed_ids)
                if not structural and not semantic:
                    self.cache.put(key, schema_name, data)
                    return DecisionResult(schema_name, data, source="claude", repaired=repaired)
                repaired = True  # next loop is the single repair attempt
            except AllowanceExceeded:
                break  # never spend overage — fall back
            except (json.JSONDecodeError, ClaudeUnavailable, subprocess.SubprocessError):
                repaired = True
                continue
        # Deterministic fallback covers every Claude-assisted stage (CLAUDE.md #13).
        data = fallback(payload)
        return DecisionResult(schema_name, data, source="fallback", repaired=repaired)


class SubprocessClaudeProvider(ClaudeDecisionProvider):
    """Calls ``claude -p --output-format json`` via an argument array (no shell).

    The prompt is passed as data; model output is treated as untrusted text and
    never executed. If the CLI is missing the base class falls back deterministically.
    """

    def __init__(self, binary: str = "claude", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.binary = binary
        self.system_prompt = (
            "You are the editorial decision component of a local video editing "
            "assistant. You receive only pre-validated transcript units, numeric "
            "features, user constraints and a Style DNA summary. Return only JSON "
            "conforming to the supplied schema. Refer only to provided ids. Never "
            "invent source footage, quotes, file paths, or UI controls. Preserve "
            "full meaning and flag uncertainty."
        )

    def _raw_call(self, schema_name: str, payload: dict[str, Any]) -> str:
        import shutil

        if not shutil.which(self.binary):
            raise ClaudeUnavailable(f"{self.binary} CLI not found")
        prompt = json.dumps(
            {"schema": schema_name, "prompt_version": PROMPT_VERSION, "input": payload},
            separators=(",", ":"),
        )
        cmd = [self.binary, "-p", "--output-format", "json", self.system_prompt + "\n" + prompt]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        if proc.returncode != 0:
            raise ClaudeUnavailable(f"claude CLI error: {proc.stderr.strip()[:200]}")
        # The CLI wraps content in an envelope; accept either raw JSON or {result:..}.
        text = proc.stdout.strip()
        try:
            env = json.loads(text)
            if isinstance(env, dict) and "result" in env:
                return env["result"] if isinstance(env["result"], str) else json.dumps(env["result"])
        except json.JSONDecodeError:
            pass
        return text
