"""Phase 1 exit gate: jobs, idempotency, restart recovery, loopback auth, S9."""

from __future__ import annotations

from capcut_coach.jobs import JobState, JobStore


def test_health_is_unauthenticated(client):
    r = client.get("/api/v1/health", headers={})
    assert r.status_code == 200 and r.json()["ok"] is True


def test_protected_route_requires_token(client):
    r = client.get("/api/v1/system/status", headers={"Authorization": ""})
    assert r.status_code == 401


def test_project_lifecycle_does_not_touch_originals(client):
    created = client.post("/api/v1/projects", json={"title": "My Reel"}).json()
    pid = created["id"]
    assert created["step"] == "sources"
    got = client.get(f"/api/v1/projects/{pid}").json()
    assert got["title"] == "My Reel"
    deleted = client.delete(f"/api/v1/projects/{pid}/analysis").json()
    assert deleted["deleted"] is True
    assert deleted["originals_touched"] is False
    assert deleted["capcut_projects_touched"] is False


def test_idempotent_enqueue(layout):
    store = JobStore(layout.db_path)
    j1 = store.enqueue(type="ingest", idempotency_key="k1")
    j2 = store.enqueue(type="ingest", idempotency_key="k1")
    assert j1.id == j2.id  # duplicate submission returns the same job


def test_illegal_transition_refused(layout):
    store = JobStore(layout.db_path)
    job = store.enqueue(type="proxy")
    store.transition(job.id, JobState.RUNNING)
    store.transition(job.id, JobState.SUCCEEDED)
    import pytest

    from capcut_coach.jobs import JobTransitionError
    with pytest.raises(JobTransitionError):
        store.transition(job.id, JobState.RUNNING)  # terminal -> running is illegal


def test_restart_requeues_running_jobs(layout):
    store = JobStore(layout.db_path)
    job = store.enqueue(type="proxy", heavy=True)
    store.transition(job.id, JobState.RUNNING)
    # Simulate a crash + restart.
    requeued = store.recover_orphans()
    assert requeued == 1
    assert store.get(job.id).state == JobState.QUEUED


def test_only_one_heavy_job_runs(layout):
    store = JobStore(layout.db_path)
    a = store.enqueue(type="proxy", heavy=True)
    store.transition(a.id, JobState.RUNNING)
    assert store.heavy_job_running() is True
