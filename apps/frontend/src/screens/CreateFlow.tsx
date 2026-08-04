import { useEffect, useRef, useState } from "react";

import {
  api, type Candidate, CoachError, type Feature, type Readiness, type Request,
  type ReviewGroup, type Slot, type Trust,
} from "../api";
import { PathField } from "../components/PathField";
import { nativePickerAvailable, pickNative } from "../native";
import {
  Button, EmptyState, Icon, ProgressSteps, SectionHeader, StatusPill,
} from "../components/ui";
import { mapJobToProgress } from "../lib/progress";

type Phase = "form" | "rendering" | "review" | "error";
const PRESETS = [
  { key: "short", label: "Short", seconds: 15, hint: "~15s" },
  { key: "standard", label: "Standard", seconds: 25, hint: "20–30s" },
  { key: "longer", label: "Longer", seconds: 50, hint: "45–60s" },
];

export function CreateFlow({ onDone }: { onDone: () => void }) {
  const [phase, setPhase] = useState<Phase>("form");
  const [folder, setFolder] = useState("");
  const [script, setScript] = useState("");
  const [logoPath, setLogoPath] = useState("");
  const [musicPath, setMusicPath] = useState("");
  const [preset, setPreset] = useState("standard");
  const [advanced, setAdvanced] = useState(false);
  const [mode, setMode] = useState("auto");
  const [maxClips, setMaxClips] = useState(8);

  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<{ title: string; body: string; detail?: string | null } | null>(null);

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [selected, setSelected] = useState<string>("enhanced");
  const [savedTo, setSavedTo] = useState<string | null>(null);
  const [job, setJob] = useState<Awaited<ReturnType<typeof api.job>> | null>(null);

  // Post-render editorial state (increments #2–#4).
  const [slots, setSlots] = useState<Slot[]>([]);
  const [reviewGroups, setReviewGroups] = useState<ReviewGroup[]>([]);
  const [requiredAcks, setRequiredAcks] = useState<string[]>([]);
  const [acked, setAcked] = useState<Set<string>>(new Set());
  const [showClips, setShowClips] = useState(false);
  const [trust, setTrust] = useState<Trust | null>(null);

  const projectId = useRef<string | null>(null);
  const poll = useRef<number | null>(null);
  const mounted = useRef(true);
  const autoSaved = useRef(false);

  useEffect(() => {
    mounted.current = true;
    void Promise.resolve(api.trust?.()).then((t) => { if (t && mounted.current) setTrust(t); }).catch(() => {});
    return () => { mounted.current = false; if (poll.current) window.clearInterval(poll.current); };
  }, []);

  const seconds = PRESETS.find((p) => p.key === preset)?.seconds ?? 25;
  const captionLines = () => script.split("\n").map((s) => s.trim()).filter(Boolean);

  async function project(): Promise<string> {
    if (!projectId.current) projectId.current = (await api.createProject("New video")).id;
    return projectId.current;
  }

  function fail(e: unknown) {
    const err = e instanceof CoachError ? e : new CoachError("unknown", String(e));
    setError({ title: "Couldn't finish that", body: err.message });
    setPhase("error");
  }

  async function check() {
    if (!folder.trim()) { setError({ title: "Add your footage first", body: "Choose the folder with this video's clips." }); return; }
    setChecking(true); setError(null);
    try {
      const pid = await project();
      const r = await api.preflight(pid, folder.trim(), {
        captions: captionLines().length ? captionLines() : undefined,
        musicPath: musicPath.trim() || undefined, logoPath: logoPath.trim() || undefined,
      });
      if (mounted.current) setReadiness(r);
    } catch (e) { fail(e); } finally { if (mounted.current) setChecking(false); }
  }

  // Fetch the clip slots + factual-review checklist for the finished video.
  async function loadReviewAids(pid: string) {
    try {
      const [s, r] = await Promise.all([api.slots(pid), api.review(pid)]);
      if (!mounted.current) return;
      setSlots(s.slots);
      setReviewGroups(r.groups);
      setRequiredAcks(r.required_ack_ids);
      setAcked(new Set());
    } catch { /* extras are best-effort; review still works without them */ }
  }

  // Watch a render/re-render job to completion, then show Review.
  function watch(jobId: string, pid: string) {
    setPhase("rendering");
    poll.current = window.setInterval(async () => {
      try {
        const j = await api.job(jobId);
        if (!mounted.current) return;
        setJob(j);
        if (j.state === "succeeded") {
          window.clearInterval(poll.current!); poll.current = null;
          const { candidates, features } = await api.candidates(pid);
          setCandidates(candidates);
          setFeatures(features ?? []);
          setSelected(candidates.find((c) => c.name === "enhanced")?.name ?? candidates[0]?.name ?? "enhanced");
          await loadReviewAids(pid);
          if (autoSaved.current) setSavedTo(trust?.default_output_dir ?? "your save folder");
          setPhase("review");
        } else if (j.state === "failed") {
          window.clearInterval(poll.current!); poll.current = null;
          const noClips = j.error_code === "autocreate_error" || j.error_code === "autopilot_error";
          setError({
            title: "The video couldn't be made",
            body: noClips
              ? "Coach couldn't find usable clips in that folder. Your originals are untouched — try a different folder."
              : "Something went wrong while rendering. Your originals are untouched — you can try again.",
            detail: j.error_detail ?? null,
          });
          setPhase("error");
        }
      } catch (e) {
        window.clearInterval(poll.current!); poll.current = null; fail(e);
      }
    }, 1000);
  }

  async function start(autopilot: boolean, autoSave = false) {
    if (!folder.trim()) { setError({ title: "Add your footage first", body: "Choose the folder with this video's clips." }); return; }
    setError(null); setSavedTo(null); autoSaved.current = false;
    try {
      const pid = await project();
      const opts = {
        captions: captionLines().length ? captionLines() : undefined,
        mode, musicPath: musicPath.trim() || undefined, logoPath: logoPath.trim() || undefined,
      };
      if (autopilot) {
        const res = await api.makeMyVideo(pid, folder.trim(), seconds, { ...opts, autoSave });
        autoSaved.current = res.auto_save;
        watch(res.job_id, pid);
      } else {
        const { job_id } = await api.autocreate(pid, folder.trim(), seconds, { ...opts, maxClips });
        watch(job_id, pid);
      }
    } catch (e) { fail(e); }
  }

  // Swap one slot's clip, then re-render and return to Review (increment #2).
  async function swap(index: number, assetId: string) {
    const pid = projectId.current;
    if (!pid) return;
    setError(null); autoSaved.current = false;
    try { const { job_id } = await api.replaceSlot(pid, index, assetId); watch(job_id, pid); }
    catch (e) { fail(e); }
  }

  const allAcked = requiredAcks.every((id) => acked.has(id));

  async function save() {
    const pid = projectId.current;
    if (!pid || !allAcked) return;
    try {
      let dest: string | undefined;
      if (nativePickerAvailable()) dest = (await pickNative("folder")) ?? undefined;
      const r = await api.approve(pid, selected, dest, [...acked]);
      setSavedTo(r.saved_to ?? "kept in this project");
      void Promise.resolve(api.trust?.()).then((t) => { if (t && mounted.current) setTrust(t); }).catch(() => {});
    } catch (e) { fail(e); }
  }

  function toggleAck(id: string) {
    setAcked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  // ---------- Rendering ----------
  if (phase === "rendering") {
    const v = mapJobToProgress(job);
    return (
      <div className="container">
        <SectionHeader title="Making your video" subtitle={v.caption} />
        <div className="card stack">
          <div className={`bar ${v.indeterminate ? "indeterminate" : ""}`}>
            <i style={{ width: v.percent !== null ? `${v.percent}%` : undefined }} />
          </div>
          <ProgressSteps steps={v.steps} />
        </div>
      </div>
    );
  }

  // ---------- Review ----------
  if (phase === "review") {
    const chosen = candidates.find((c) => c.name === selected) ?? candidates[0];
    const why = selected === "enhanced"
      ? "Enhanced is Coach's pick — a clean cut with tasteful polish and readable captions."
      : selected === "bold"
        ? "Bold leads with your strongest shot and a punchier look."
        : "Clean is the most conservative, straight-cut version.";
    return (
      <div className="container">
        <SectionHeader title="Your video is ready" subtitle="Pick a version, tweak any shot, then save." />
        <div className="two-col">
          <div className="stack">
            <div className="player-wrap">
              {chosen && <video className="player" src={chosen.url} controls playsInline />}
            </div>
            <div className="row">
              {candidates.map((c) => (
                <button key={c.name} className="chip" aria-pressed={c.name === selected}
                  onClick={() => setSelected(c.name)} style={{ textTransform: "capitalize" }}>
                  {c.name}{c.name === "enhanced" ? " · recommended" : ""}
                </button>
              ))}
            </div>

            {slots.length > 0 && (
              <details className="card" open={showClips}
                onToggle={(e) => setShowClips((e.target as HTMLDetailsElement).open)}>
                <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                  Change a clip <span className="muted small">({slots.length} shots)</span>
                </summary>
                <div className="stack" style={{ marginTop: 12 }}>
                  {slots.map((s) => (
                    <div key={s.index} className="source">
                      <div className="ico"><Icon name="film" /></div>
                      <div className="grow">
                        <div className="between">
                          <h3 style={{ margin: 0 }}>Shot {s.index + 1}</h3>
                          <span className="muted small">{s.label}</span>
                        </div>
                        {s.caption && <div className="small muted" style={{ margin: "2px 0 6px" }}>“{s.caption}”</div>}
                        {s.alternatives.length > 0 ? (
                          <div className="row" style={{ flexWrap: "wrap" }}>
                            <span className="small muted" style={{ alignSelf: "center" }}>Swap for:</span>
                            {s.alternatives.map((a) => (
                              <button key={a.asset_id} className="chip" onClick={() => swap(s.index, a.asset_id)}
                                title={a.reason}>{a.label}</button>
                            ))}
                          </div>
                        ) : <div className="small muted">No other clip fits this spot.</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>

          <div className="stack">
            <div className="card stack">
              <h2>Why Coach chose this</h2>
              <p className="muted small" style={{ margin: 0 }}>{why}</p>
            </div>

            {features.length > 0 && (
              <div className="card stack">
                <h2>What Coach did</h2>
                <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none" }}>
                  {features.map((f) => (
                    <li key={f.key} className="row" style={{ alignItems: "flex-start", gap: 8, padding: "4px 0" }}>
                      <span style={{ marginTop: 2, color: `var(--${f.applied ? "success" : "warning"})` }}>
                        <Icon name={f.applied ? "check" : "alert"} size={16} />
                      </span>
                      <span><strong className="small">{f.title}</strong>
                        <span className="small muted" style={{ display: "block" }}>{f.detail}</span></span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {reviewGroups.length > 0 && (
              <div className="card stack">
                <h2>Before you save</h2>
                <p className="muted small" style={{ margin: 0 }}>
                  Coach never claims this is publish-ready. Confirm the essentials — you own what you publish.
                </p>
                {reviewGroups.map((g) => (
                  <div key={g.key} className="stack" style={{ gap: 6 }}>
                    <strong className="small">{g.title}</strong>
                    {g.note && <p className="small muted" style={{ margin: 0 }}>{g.note}</p>}
                    {g.items.map((it) => (
                      it.requires_ack ? (
                        <label key={it.id} className="row" style={{ alignItems: "flex-start", gap: 8, cursor: "pointer" }}>
                          <input type="checkbox" checked={acked.has(it.id)} onChange={() => toggleAck(it.id)}
                            style={{ marginTop: 3 }} />
                          <span><span>{it.label}</span>
                            <span className="small muted" style={{ display: "block" }}>{it.detail}</span></span>
                        </label>
                      ) : (
                        <div key={it.id} className="small muted" style={{ paddingLeft: 24 }}>
                          <Icon name="info" size={13} /> {it.label} — {it.detail}
                        </div>
                      )
                    ))}
                  </div>
                ))}
              </div>
            )}

            <Button variant="primary" size="lg" icon="check" onClick={save} disabled={!allAcked}>Save video</Button>
            {!allAcked && requiredAcks.length > 0 && (
              <p className="small muted center" style={{ margin: 0 }}>Confirm the checked items above to save.</p>
            )}
            {savedTo && (
              <div className="pill ok"><Icon name="check" size={14} /> Saved · {savedTo}</div>
            )}
            <Button icon="plus" onClick={() => { setPhase("form"); setCandidates([]); setSavedTo(null); setSlots([]); setReviewGroups([]); setFeatures([]); }}>
              Make another
            </Button>
            <Button variant="ghost" onClick={onDone}>Back to projects</Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- Error ----------
  if (phase === "error") {
    return (
      <div className="container">
        <EmptyState icon="alert" title={error?.title ?? "Something went wrong"}
          body={<>{error?.body}<br /><span className="small">Your original footage is safe and unchanged.</span></>}
          action={<Button variant="primary" onClick={() => setPhase("form")}>Try again</Button>} />
        {error?.detail && (
          <details className="card" style={{ marginTop: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>Technical details</summary>
            <pre className="small" style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", margin: "10px 0 0" }}>
              {error.detail}
            </pre>
          </details>
        )}
      </div>
    );
  }

  // ---------- Form ----------
  const canCreate = folder.trim().length > 0;
  return (
    <div className="container">
      <SectionHeader title="Make a video"
        subtitle="Add your clips. Coach handles shots, story, captions and music automatically." />
      <div className="two-col">
        <div className="stack">
          <PathField icon="folder" title="Raw footage" kind="folder" required
            value={folder} onChange={setFolder} hint="The folder with this video's clips (a .zip works too)." />
          <div className="card field">
            <label htmlFor="script">Script or message <span className="muted small">(optional)</span></label>
            <textarea id="script" className="textarea" value={script} onChange={(e) => setScript(e.target.value)}
              placeholder={"One short line per shot, e.g.\nA moment for you\nTo relax\nBook today"} />
          </div>
          <PathField icon="image" title="Brand logo" kind="image"
            value={logoPath} onChange={setLogoPath} hint="Optional — adds a branded ending." />

          <details className="card" open={advanced} onToggle={(e) => setAdvanced((e.target as HTMLDetailsElement).open)}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>Advanced options</summary>
            <div className="stack" style={{ marginTop: 16 }}>
              <PathField icon="music" title="Specific music track" kind="audio"
                value={musicPath} onChange={setMusicPath} hint="Use a track you own or that's licensed." />
              <div className="field">
                <label htmlFor="mode">Edit type</label>
                <select id="mode" className="select" value={mode} onChange={(e) => setMode(e.target.value)}>
                  <option value="auto">Let Coach decide</option>
                  <option value="montage">Montage / B-roll</option>
                  <option value="talking">Talking to camera</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="clips">Most shots to include: {maxClips}</label>
                <input id="clips" type="range" min={3} max={16} value={maxClips}
                  onChange={(e) => setMaxClips(Number(e.target.value))} />
              </div>
            </div>
          </details>
        </div>

        <div className="stack">
          <div className="card stack">
            <h2>Length</h2>
            <div className="row">
              {PRESETS.map((p) => (
                <button key={p.key} className="chip" aria-pressed={preset === p.key}
                  onClick={() => setPreset(p.key)}>{p.label} <span className="muted small">{p.hint}</span></button>
              ))}
            </div>
          </div>
          <div className="card stack">
            <h2>Coach will do this automatically</h2>
            <ul className="small muted" style={{ margin: 0, paddingLeft: 18 }}>
              <li>Pick the strongest moments and reframe on the subject</li>
              <li>Build a Clean, Enhanced and Bold version</li>
              <li>Add captions and approved music when available</li>
              <li>Render a finished vertical MP4 — no CapCut needed</li>
            </ul>
          </div>

          {readiness && <ReadinessPanel r={readiness} />}

          <Button onClick={check} disabled={checking || !canCreate}>
            {checking ? "Checking…" : "Smart Check"}
          </Button>

          {trust?.ready_for_one_tap ? (
            <>
              <Button variant="primary" size="lg" icon="sparkles" onClick={() => start(true, true)} disabled={!canCreate}>
                Make &amp; save automatically
              </Button>
              <Button variant="ghost" onClick={() => start(true, false)} disabled={!canCreate}>
                Review before saving
              </Button>
            </>
          ) : (
            <>
              <Button variant="primary" size="lg" icon="sparkles" onClick={() => start(true, false)} disabled={!canCreate}>
                Make my video
              </Button>
              <Button variant="ghost" onClick={() => start(false, false)} disabled={!canCreate}>
                Review 3 versions instead
              </Button>
            </>
          )}

          {trust && !trust.autopilot_unlocked && (
            <p className="small muted center" style={{ margin: 0 }}>
              One-tap auto-save unlocks after {trust.threshold} approved videos ({trust.approvals}/{trust.threshold}).
            </p>
          )}
          {trust && trust.autopilot_unlocked && !trust.default_output_dir && (
            <p className="small muted center" style={{ margin: 0 }}>
              Set a save folder in Settings to turn on one-tap auto-save.
            </p>
          )}
          {!canCreate && <p className="small muted center" style={{ margin: 0 }}>Add a footage folder to continue.</p>}
          {error && <div className="pill bad"><Icon name="alert" size={14} /> {error.body}</div>}
        </div>
      </div>
    </div>
  );
}

function ReadyItem({ r }: { r: Request }) {
  return (
    <div className="card" style={{ borderLeft: `4px solid var(--${r.blocking ? "danger" : "warning"})`, padding: 16 }}>
      <strong>{r.what_needed}</strong>
      <p className="small muted" style={{ margin: "4px 0" }}>{r.why}</p>
      {r.recording_direction && <p className="small" style={{ margin: "4px 0" }}>Film: {r.recording_direction}</p>}
      <div className="small muted">Best: {r.recommended_action} · Or: {r.fallback}</div>
    </div>
  );
}

function ReadinessPanel({ r }: { r: Readiness }) {
  const tone = r.status === "READY" ? "ok" : r.status === "NEEDS_HELP" ? "bad" : "warn";
  return (
    <div className="card stack">
      <div className="between">
        <h2 style={{ margin: 0 }}>Smart Check</h2>
        <StatusPill tone={tone}>{r.headline}</StatusPill>
      </div>
      {r.blocking_requests.length > 0 && (
        <div className="stack"><strong className="small">Needed</strong>
          {r.blocking_requests.map((rq, i) => <ReadyItem key={`b${i}`} r={rq} />)}</div>
      )}
      {r.suggestions.length > 0 && (
        <div className="stack"><strong className="small">Suggestions</strong>
          {r.suggestions.map((rq, i) => <ReadyItem key={`s${i}`} r={rq} />)}</div>
      )}
    </div>
  );
}
