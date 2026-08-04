"""Increments #2 & #3 over HTTP: slots, clip swap, review, and the approve gate."""

from __future__ import annotations

import json

from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment

US = 1_000_000


def _seed(layout, pid: str, *, music: bool = False) -> None:
    """Write the persisted edit state Coach would have produced at render time."""
    out = layout.project_dir(pid) / "candidates"
    out.mkdir(parents=True, exist_ok=True)
    segs = [
        Segment(id=f"seg{i}", asset_id=f"a{i}", source_start_us=0,
                source_duration_us=2 * US, timeline_start_us=i * 2 * US,
                timeline_duration_us=2 * US, confidence=0.6)
        for i in range(3)
    ]
    caps = [Caption(id="c0", text="Buy one get one free", start_us=0, duration_us=2 * US)]
    plan = EditPlan(id="e", project_id=pid, segments=segs, captions=caps)
    (out / "plan.json").write_text(plan.model_dump_json(), "utf-8")
    catalog = [{"id": f"a{i}", "path": f"/tmp/a{i}.mp4", "name": f"clip_{i}.mp4",
                "duration_us": 5 * US, "has_audio": True} for i in range(5)]
    (out / "catalog.json").write_text(json.dumps(catalog), "utf-8")
    (out / "analyses.json").write_text(json.dumps(
        {"a3": {"score": 0.9, "best_start_us": 0, "crop_x_norm": 0.1}}), "utf-8")
    (out / "render_context.json").write_text(json.dumps(
        {"music_path": "/tmp/track.mp3" if music else None,
         "music_name": "track.mp3" if music else None,
         "logo_path": None, "voice_led": False, "target_us": 6 * US}), "utf-8")
    for name in ("clean", "enhanced", "bold"):
        (out / f"{name}.mp4").write_bytes(b"\x00" * 32)  # stand-in rendered file
    (out / "candidates.json").write_text(json.dumps(
        [{"name": n, "file": f"{n}.mp4", "ok": True, "detail": "ok"}
         for n in ("clean", "enhanced", "bold")]), "utf-8")


def test_slots_lists_alternatives(client, layout):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid)
    slots = client.get(f"/api/v1/projects/{pid}/slots").json()["slots"]
    assert [s["index"] for s in slots] == [0, 1, 2]
    mid_alts = {a["asset_id"] for a in slots[1]["alternatives"]}
    assert {"a3", "a4"} <= mid_alts and "a1" not in mid_alts


def test_replace_slot_updates_plan_and_starts_job(client, layout):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid)
    r = client.post(f"/api/v1/projects/{pid}/slots/1/replace", json={"asset_id": "a3"})
    assert r.status_code == 202 and "job_id" in r.json()
    plan_path = layout.project_dir(pid) / "candidates" / "plan.json"
    updated = EditPlan.model_validate_json(plan_path.read_text("utf-8"))
    swapped = sorted(updated.segments, key=lambda s: s.timeline_start_us)[1]
    assert swapped.asset_id == "a3" and swapped.reason == "user_swapped_clip"


def test_replace_rejects_unknown_clip(client, layout):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid)
    r = client.post(f"/api/v1/projects/{pid}/slots/1/replace", json={"asset_id": "nope"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "unknown_clip"


def test_review_groups_expose_required_claims(client, layout):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid, music=True)
    data = client.get(f"/api/v1/projects/{pid}/review").json()
    keys = {g["key"] for g in data["groups"]}
    assert {"claims", "music"} <= keys
    assert "claim-0" in data["required_ack_ids"]
    assert "music-rights" in data["required_ack_ids"]


def test_approve_blocked_until_required_items_acknowledged(client, layout):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid)
    blocked = client.post(f"/api/v1/projects/{pid}/approve", json={"candidate": "enhanced"})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "review_incomplete"
    assert "claim-0" in blocked.json()["error"]["missing"]

    ok = client.post(f"/api/v1/projects/{pid}/approve",
                     json={"candidate": "enhanced", "acknowledged": ["claim-0"]})
    assert ok.status_code == 200 and ok.json()["approved"] == "enhanced"
