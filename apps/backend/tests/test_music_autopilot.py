"""Full Autopilot: rights-gated music, selection, candidate scoring, no ripping."""

from __future__ import annotations

from pathlib import Path

from capcut_coach.autopilot import choose_best
from capcut_coach.music.schemas import MusicAsset, RightsStatus
from capcut_coach.music.select import select_music


def _asset(name, *, bpm, dur, energy=0.6, vocals=False,
           status=RightsStatus.OWNER_APPROVED):
    return MusicAsset(id=name, content_hash=name, path=f"/approved/{name}.mp3", title=name,
                      rights_status=status, bpm=bpm, duration_s=dur, energy=energy, vocals=vocals)


# ---------- Rights gate + selection ----------
def test_only_rights_eligible_tracks_are_selectable():
    ineligible = _asset("scraped", bpm=120, dur=60, status=RightsStatus.INELIGIBLE)
    ok = _asset("owned", bpm=120, dur=60)
    sel = select_music([ineligible, ok], target_seconds=20)
    assert sel.chosen is not None and sel.chosen.id == "owned"
    # The ineligible track never appears anywhere in the selection.
    assert all(a.id != "scraped" for a in [sel.chosen, *sel.alternatives])


def test_selection_is_reproducible_and_offers_alternatives():
    assets = [_asset(f"t{i}", bpm=100 + i * 8, dur=40 + i * 5) for i in range(4)]
    a = select_music(assets, target_seconds=20, prefer_bpm=120)
    b = select_music(assets, target_seconds=20, prefer_bpm=120)
    assert a.chosen.id == b.chosen.id                 # deterministic
    assert 1 <= len(a.alternatives) <= 2              # keeps alternatives


def test_dialogue_edit_avoids_vocal_tracks():
    vocal = _asset("song", bpm=120, dur=60, vocals=True)
    instr = _asset("bed", bpm=120, dur=60, vocals=False)
    sel = select_music([vocal, instr], target_seconds=20, avoid_vocals=True)
    assert sel.chosen.id == "bed"


def test_no_eligible_music_returns_none_not_error():
    sel = select_music([], target_seconds=20)
    assert sel.chosen is None and "No rights-approved" in sel.reason


# ---------- Safety: no network / music-ripping code path (doc 20 acceptance) ----------
def test_music_module_has_no_network_or_download_code():
    import capcut_coach.music as musicpkg
    root = Path(musicpkg.__file__).parent
    banned = ("import requests", "import urllib", "urllib.request", "http://", "https://",
              "youtube", "spotify", "tiktok", "yt-dlp", "youtube_dl", "urlopen", "socket",
              "wget", "curl ")
    for py in root.glob("*.py"):
        text = py.read_text("utf-8").lower()
        for token in banned:
            assert token not in text, f"{py.name} contains forbidden token {token!r}"


# ---------- Autopilot candidate scoring ----------
def test_choose_best_prefers_richer_candidate():
    from capcut_coach.render.candidates import build_candidates
    from capcut_coach.render.graph import Outro
    from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment

    plan = EditPlan(id="e", project_id="p", segments=[
        Segment(id="s1", asset_id="a1", source_start_us=0, source_duration_us=2_000_000,
                timeline_start_us=0, timeline_duration_us=2_000_000, confidence=0.9),
        Segment(id="s2", asset_id="a2", source_start_us=0, source_duration_us=2_000_000,
                timeline_start_us=2_000_000, timeline_duration_us=2_000_000, confidence=0.6)],
        captions=[Caption(id="c1", text="Hello there", start_us=0, duration_us=2_000_000)])
    cands = build_candidates(plan, {"a1": Path("/x/a1.mp4"), "a2": Path("/x/a2.mp4")})
    for c in cands:  # give every candidate a soundtrack + outro
        c.graph.music_path = Path("/approved/track.mp3")
        c.graph.outro = Outro(logo_path=Path("/brand/logo.png"))
    decision = choose_best(cands)
    assert decision.chosen in {"enhanced", "bold"}    # richer than plain Clean
    assert decision.score_of("enhanced") >= decision.score_of("clean")
