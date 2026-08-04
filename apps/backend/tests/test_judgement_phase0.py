"""Human Judgement Engine — Phase 0 foundations (schemas, calibration, story,
confidence, evaluation harness). All pure and media-independent (add-on §6–§18)."""

from __future__ import annotations

from pathlib import Path

import pytest

from capcut_coach.judgement import (
    Action, Confidence, TechnicalEvidence, build_baseline, decide,
    extract_immutable_facts, facts_preserved, hard_failures, load_manifest,
    parse_beats, parse_semantic, usability_score,
)
from capcut_coach.judgement.evaluation import ManifestError

US = 1_000_000


# ---------- schemas ----------

def test_semantic_rejects_unknown_keys_and_falls_back():
    good = parse_semantic({"setting": "room", "shot_type": "close_up", "usable": True})
    assert good is not None and good.usable is True
    # A hallucinated/extra field must be rejected so we fall back to Level A.
    assert parse_semantic({"setting": "room", "made_up_claim": "cures acne"}) is None
    assert parse_semantic("not even a dict") is None


def test_evidence_carries_provenance_and_version():
    ev = TechnicalEvidence(extractor_version="p1", confidence=0.4, focus_median=120.0)
    assert ev.schema_version >= 1 and ev.extractor_version == "p1"


# ---------- calibration (§7.3) ----------

def test_hard_blockers_reject_unusable_windows():
    assert "near_black" in hard_failures(TechnicalEvidence(black_frame_ratio=0.8))
    assert "blown_highlights" in hard_failures(TechnicalEvidence(clipped_highlight_ratio=0.7))
    assert hard_failures(TechnicalEvidence(focus_median=50)) == []  # merely soft ≠ blocked


def test_dark_but_intentional_footage_is_not_rejected():
    # A consistently dim project: low brightness, but sharp and clean → still usable.
    dim = TechnicalEvidence(focus_median=140.0, underexposed_ratio=0.6,
                            clipped_shadow_ratio=0.1)
    base = build_baseline([130.0, 140.0, 150.0, 135.0])
    score = usability_score(dim, focus_baseline=base)
    assert score > 0.4  # not punished for artistic darkness (no clipping blocker)


def test_within_clip_max_cannot_inflate_a_soft_clip():
    base = build_baseline([200.0, 210.0, 205.0, 60.0])  # one soft clip in a sharp project
    soft = usability_score(TechnicalEvidence(focus_median=60.0), focus_baseline=base)
    sharp = usability_score(TechnicalEvidence(focus_median=205.0), focus_baseline=base)
    assert sharp > soft  # calibrated against the project, not the clip's own frames


# ---------- story beats (§8) ----------

def test_immutable_facts_are_extracted():
    facts = extract_immutable_facts("Book today and save 50% — only £29")
    joined = " ".join(facts).lower()
    assert "50%" in joined and "£29" in joined and "book" in joined and "save" in joined


def test_cta_and_offer_beats_are_required():
    beats = parse_beats("A calm moment for you\nRelax and unwind\nBook today for 20% off")
    assert [b.purpose for b in beats][0] == "hook"
    cta = beats[-1]
    assert cta.purpose == "cta" and cta.required is True
    assert any("20%" in f for f in cta.immutable_facts)


def test_facts_preserved_guard():
    facts = ["£29", "50%"]
    assert facts_preserved(facts, "Just £29 today — 50% off") is True
    assert facts_preserved(facts, "A great deal today") is False  # dropped facts → reject


# ---------- confidence policy (§11) ----------

def test_confidence_automates_only_with_clear_margin_and_no_risk():
    d = decide(top_score=0.8, runner_up_score=0.5, required_coverage_complete=True,
               has_blocker=False, facts_uncertain=False)
    assert d.confidence == Confidence.HIGH and d.action == Action.AUTOMATE


def test_confidence_asks_when_required_beat_missing():
    d = decide(top_score=0.9, runner_up_score=0.1, required_coverage_complete=False,
               has_blocker=False, facts_uncertain=False)
    assert d.confidence == Confidence.LOW and d.action == Action.ASK_USER


def test_confidence_recommends_on_a_close_call():
    d = decide(top_score=0.60, runner_up_score=0.58, required_coverage_complete=True,
               has_blocker=False, facts_uncertain=False)
    assert d.confidence == Confidence.MEDIUM and d.action == Action.RECOMMEND


# ---------- evaluation manifest (§17/§18) ----------

def test_manifest_loads_and_enforces_approved_roots(tmp_path: Path):
    root = tmp_path / "footage"
    root.mkdir()
    manifest = tmp_path / "eval.local.json"
    manifest.write_text(
        '{"version":1,"examples":[{"id":"ex1","style":"montage",'
        f'"raw_root":"{root}"}}]}}', "utf-8")
    m = load_manifest(manifest, approved_roots=[tmp_path])
    assert m.examples[0].id == "ex1"


def test_manifest_refuses_path_escaping_roots(tmp_path: Path):
    manifest = tmp_path / "eval.local.json"
    manifest.write_text(
        '{"version":1,"examples":[{"id":"x","raw_root":"/etc"}]}', "utf-8")
    with pytest.raises(ManifestError):
        load_manifest(manifest, approved_roots=[tmp_path])
