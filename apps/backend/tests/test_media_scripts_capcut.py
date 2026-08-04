"""Phase 2 + 7 + 0: SRT, cache, script pack, compatibility, canary, handoff, QC."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from capcut_coach.capcut.canary import (
    CanaryPreconditions,
    CanaryRefused,
    backup_project,
    hash_tree,
    restore_project,
    run_canary_once,
)
from capcut_coach.capcut.compatibility import (
    CompatibilityRecord,
    CompatibilityStatus,
    can_mutate,
    effective_status_after_update,
)
from capcut_coach.capcut.handoff import build_handoff
from capcut_coach.media.cache import ContentCache, cache_key, hash_file
from capcut_coach.media.srt import captions_to_srt, validate_srt
from capcut_coach.qc import run_deterministic_qc
from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment
from capcut_coach.scripts_pack.parser import UnsafeArchiveError, parse_script_pack, safe_extract_zip


# ---------- SRT (F4) ----------
def test_srt_is_utf8_and_non_overlapping():
    caps = [Caption(id="c1", text="Hello", start_us=0, duration_us=1_000_000),
            Caption(id="c2", text="world", start_us=1_000_000, duration_us=1_000_000)]
    text = captions_to_srt(caps)
    assert "-->" in text
    assert validate_srt(text) == []


def test_srt_rejects_overlap():
    caps = [Caption(id="c1", text="a", start_us=0, duration_us=2_000_000),
            Caption(id="c2", text="b", start_us=1_000_000, duration_us=1_000_000)]
    with pytest.raises(ValueError):
        captions_to_srt(caps)


# ---------- Cache (F3) ----------
def test_cache_key_is_deterministic_and_config_sensitive():
    k1 = cache_key(content_hash="abc", tool="whisper", config={"model": "base"})
    k2 = cache_key(content_hash="abc", tool="whisper", config={"model": "base"})
    k3 = cache_key(content_hash="abc", tool="whisper", config={"model": "small"})
    assert k1 == k2 and k1 != k3


def test_cache_put_get_and_eviction(tmp_path: Path):
    cache = ContentCache(tmp_path / "cache")
    f = tmp_path / "out.bin"
    f.write_bytes(b"x" * 1000)
    cache.put("k1", kind="proxy", path=f)
    assert cache.get("k1") is not None
    pinned = tmp_path / "pinned.bin"
    pinned.write_bytes(b"y" * 1000)
    cache.put("k2", kind="proxy", path=pinned, pinned=True)
    removed = cache.evict_to_budget(0)
    assert "k1" in removed and "k2" not in removed  # pinned survives


def test_hash_file_streaming(tmp_path: Path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello")
    import hashlib
    assert hash_file(f) == hashlib.sha256(b"hello").hexdigest()


# ---------- Script pack (F4A) ----------
def _make_zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_safe_extract_rejects_traversal(tmp_path: Path):
    zbytes = _make_zip({"../evil.txt": b"x"})
    zpath = tmp_path / "bad.zip"
    zpath.write_bytes(zbytes)
    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(zpath, tmp_path / "out")


def test_script_pack_parses_reels_and_retains_unknown(tmp_path: Path):
    script = (
        "Reel 1: Intro\n"
        "Shot 1 00:00-00:05 close-up: Welcome back everyone\n"
        "Overlay: Subscribe now\n"
        "Cutaway b-roll of the product\n"
        "Transition: fade\n"
        "Some freeform note the parser cannot classify\n"
        "End card CTA: follow for more\n"
    )
    zbytes = _make_zip({"my script/reel one.txt": script.encode()})
    zpath = tmp_path / "pack.zip"
    zpath.write_bytes(zbytes)
    plan = parse_script_pack(zpath, tmp_path / "work")
    counts = plan.counts()
    assert plan.reels >= 1
    assert counts.get("reel", 0) >= 1
    assert counts.get("overlay", 0) >= 1
    assert counts.get("end_card", 0) >= 1
    assert plan.unparsed  # freeform line retained, not dropped


# ---------- Compatibility (S3) ----------
def _record(status=CompatibilityStatus.CANARY_REQUIRED, runs=0):
    return CompatibilityRecord(
        capcut_semver="3.1.0", build_number="4200", macos_version="14.5",
        app_source="cc", schema_version="9", timeline_filename="draft_content.json",
        status=status, canary_runs_passed=runs,
    )


def test_direct_write_refused_without_canary():
    rec = _record(CompatibilityStatus.CANARY_REQUIRED)
    ok, reason = can_mutate(rec, direct_write_enabled=True, capcut_running=False,
                            target_is_duplicate=True)
    assert not ok


def test_direct_write_refused_while_capcut_running():
    rec = _record(CompatibilityStatus.DIRECT_WRITE_CAPTION_ONLY, runs=10)
    ok, reason = can_mutate(rec, direct_write_enabled=True, capcut_running=True,
                            target_is_duplicate=True)
    assert not ok and "running" in reason


def test_direct_write_refused_on_original():
    rec = _record(CompatibilityStatus.DIRECT_WRITE_CAPTION_ONLY, runs=10)
    ok, reason = can_mutate(rec, direct_write_enabled=True, capcut_running=False,
                            target_is_duplicate=False)
    assert not ok and "duplicate" in reason


def test_version_update_drops_status():
    rec = _record(CompatibilityStatus.DIRECT_WRITE_TEMPLATE_CLONE, runs=10)
    assert effective_status_after_update(rec, "3.2.0", "4300") == \
        CompatibilityStatus.CANARY_REQUIRED


# ---------- Canary (S5/S6) ----------
def test_canary_refuses_on_original():
    pre = CanaryPreconditions(capcut_closed=True, is_duplicate=False,
                              backup_exists=True, version_supported=True)
    with pytest.raises(CanaryRefused):
        pre.check()


def test_canary_backup_restore_preserves_hashes(tmp_path: Path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "draft_content.json").write_text('{"a":1}')
    backup = tmp_path / "backup"
    pre = CanaryPreconditions(True, True, True, True)
    result = run_canary_once(run_index=1, project_dir=proj, backup_dir=backup,
                             pre=pre, mutate=None)
    assert result.restored and result.pre_hashes_match and result.mutated is False


# ---------- Handoff (F9) ----------
def test_handoff_builds_valid_srt_and_manifest(tmp_path: Path):
    plan = EditPlan(id="e1", project_id="p1",
                    segments=[Segment(id="s1", asset_id="a1", source_start_us=0,
                                      source_duration_us=1_000_000, timeline_start_us=0,
                                      timeline_duration_us=1_000_000, role="hook")],
                    captions=[Caption(id="c1", text="Hi", start_us=0, duration_us=1_000_000)])
    result = build_handoff(plan, asset_paths={}, out_dir=tmp_path / "handoff",
                           project_title="Demo")
    assert result.srt_valid
    assert result.manifest_path.exists() and result.guide_path.exists()
    assert result.clips_planned == 1


# ---------- QC (F12) ----------
def test_qc_flags_reading_speed_and_missing_cta():
    plan = EditPlan(id="e1", project_id="p1",
                    segments=[Segment(id="s1", asset_id="a1", source_start_us=0,
                                      source_duration_us=500_000, timeline_start_us=0,
                                      timeline_duration_us=500_000)],
                    captions=[Caption(id="c1", text="This is a very long caption to read",
                                      start_us=0, duration_us=500_000)])
    findings = run_deterministic_qc(plan)
    codes = {f.code for f in findings}
    assert "reading_speed" in codes
    assert "missing_cta" in codes
