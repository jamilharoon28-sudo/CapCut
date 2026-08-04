"""Phase 4 / F8 + S8: Claude output validation, caching, fallback, overage guard."""

from __future__ import annotations

from capcut_coach.claude.fallbacks import FALLBACKS
from capcut_coach.claude.provider import (
    AllowanceMeter,
    ClaudeDecisionProvider,
    InMemoryDecisionCache,
)


class ScriptedProvider(ClaudeDecisionProvider):
    """Test double returning canned raw strings in sequence."""

    def __init__(self, responses, **kw):
        super().__init__(**kw)
        self._responses = list(responses)
        self.calls = 0

    def _raw_call(self, schema_name, payload):
        self.calls += 1
        return self._responses.pop(0)


PAYLOAD = {
    "candidates": [{"id": "c1", "confidence": 0.4}, {"id": "c2", "confidence": 0.9}],
}


def test_valid_response_accepted_and_cached():
    good = '{"ranking":[{"candidate_id":"c1","rank":1,"reason":"x","confidence":0.5}]}'
    p = ScriptedProvider([good], cache=InMemoryDecisionCache())
    r1 = p.decide("hook_ranking", PAYLOAD, allowed_id_keys=("candidates",),
                  fallback=FALLBACKS["hook_ranking"])
    assert r1.source == "claude"
    # Second identical request hits cache — no new call.
    r2 = p.decide("hook_ranking", PAYLOAD, allowed_id_keys=("candidates",),
                  fallback=FALLBACKS["hook_ranking"])
    assert r2.source == "cache"
    assert p.calls == 1


def test_unknown_id_triggers_repair_then_fallback():
    bad = '{"ranking":[{"candidate_id":"ghost","rank":1,"reason":"x","confidence":0.5}]}'
    p = ScriptedProvider([bad, bad], cache=InMemoryDecisionCache())
    r = p.decide("hook_ranking", PAYLOAD, allowed_id_keys=("candidates",),
                 fallback=FALLBACKS["hook_ranking"])
    assert r.source == "fallback"
    assert r.repaired is True
    # Deterministic fallback ranks c2 (0.9) above c1 (0.4).
    assert r.data["ranking"][0]["candidate_id"] == "c2"


def test_malformed_json_falls_back():
    p = ScriptedProvider(["not json", "still not json"], cache=InMemoryDecisionCache())
    r = p.decide("hook_ranking", PAYLOAD, allowed_id_keys=("candidates",),
                 fallback=FALLBACKS["hook_ranking"])
    assert r.source == "fallback"


def test_overage_guard_hard_stops_and_falls_back():
    good = '{"ranking":[{"candidate_id":"c1","rank":1,"reason":"x","confidence":0.5}]}'
    meter = AllowanceMeter(limit=0, overage_enabled=False)
    p = ScriptedProvider([good], allowance=meter, cache=InMemoryDecisionCache())
    r = p.decide("hook_ranking", PAYLOAD, allowed_id_keys=("candidates",),
                 fallback=FALLBACKS["hook_ranking"])
    assert r.source == "fallback"
    assert p.calls == 0  # never called the model past the allowance


def test_disabled_provider_uses_fallback_only():
    p = ScriptedProvider([], enabled=False)
    r = p.decide("narrative_plan",
                 {"units": [{"id": "u1", "duration_us": 1000},
                            {"id": "u2", "duration_us": 1000}],
                  "target_duration_us": 5000},
                 allowed_id_keys=("units",), fallback=FALLBACKS["narrative_plan"])
    assert r.source == "fallback"
    assert r.data["ordered_unit_ids"] == ["u1", "u2"]
