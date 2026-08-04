"""Increment #4: earned trust unlocks one-tap auto-save; it's gated until then."""

from __future__ import annotations

from capcut_coach.approvals import approval_count, record_approval, trust_state


def test_trust_state_unlocks_at_threshold(layout):
    db = layout.db_path
    assert trust_state(db)["autopilot_unlocked"] is False
    for _ in range(5):
        record_approval(db, "p1", "enhanced")
    assert approval_count(db) == 5
    st = trust_state(db, threshold=5)
    assert st["autopilot_unlocked"] is True and st["remaining"] == 0


def test_trust_endpoint_reports_progress(client):
    st = client.get("/api/v1/system/trust").json()
    assert st["approvals"] == 0
    assert st["autopilot_unlocked"] is False
    assert st["ready_for_one_tap"] is False


def test_default_output_rejects_cloud_and_accepts_local(client, tmp_path):
    cloud = "/Users/x/Library/CloudStorage/GoogleDrive-a/My Drive"
    bad = client.post("/api/v1/system/default-output", json={"path": cloud})
    assert bad.status_code == 400 and bad.json()["error"]["code"] in ("cloud_readonly", "bad_folder")

    good = client.post("/api/v1/system/default-output", json={"path": str(tmp_path)})
    assert good.status_code == 200 and good.json()["default_output_dir"] == str(tmp_path)

    cleared = client.post("/api/v1/system/default-output", json={"path": None})
    assert cleared.json()["default_output_dir"] is None


def test_one_tap_auto_save_is_gated_until_trusted(client, layout, tmp_path):
    # Destination set, but no approvals yet → one-tap stays off.
    client.post("/api/v1/system/default-output", json={"path": str(tmp_path)})
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    r = client.post(f"/api/v1/projects/{pid}/make-my-video",
                    json={"media_dir": str(tmp_path), "auto_save": True})
    assert r.status_code == 202 and r.json()["auto_save"] is False

    # Earn trust, then one-tap is honoured.
    for _ in range(5):
        record_approval(layout.db_path, "seed", "enhanced")
    r2 = client.post(f"/api/v1/projects/{pid}/make-my-video",
                     json={"media_dir": str(tmp_path), "auto_save": True})
    assert r2.status_code == 202 and r2.json()["auto_save"] is True


def test_manual_approve_counts_toward_trust(client, layout):
    from tests.test_editing_api import _seed

    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    _seed(layout, pid)
    client.post(f"/api/v1/projects/{pid}/approve",
                json={"candidate": "clean", "acknowledged": ["claim-0"]})
    assert client.get("/api/v1/system/trust").json()["approvals"] == 1
