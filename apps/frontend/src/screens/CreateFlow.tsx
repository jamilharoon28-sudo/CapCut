import { useEffect, useRef, useState } from "react";

import { api, type Candidate, CoachError, type Readiness, type Request } from "../api";
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
  const [error, setError] = useState<{ title: string; body: string } | null>(null);

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<string>("enhanced");
  const [savedTo, setSavedTo] = useState<string | null>(null);
  const [job, setJob] = useState<Awaited<ReturnType<typeof api.job>> | null>(null);

  const projectId = useRef<string | null>(null);
  const poll = useRef<number | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
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

  async function start(autopilot: boolean) {
    if (!folder.trim()) { setError({ title: "Add your footage first", body: "Choose the folder with this video's clips." }); return; }
    setError(null);
    try {
      const pid = await project();
      const opts = {
        captions: captionLines().length ? captionLines() : undefined,
        mode, musicPath: musicPath.trim() || undefined, logoPath: logoPath.trim() || undefined,
      };
      const { job_id } = autopilot
        ? await api.makeMyVideo(pid, folder.trim(), seconds, opts)
        : await api.autocreate(pid, folder.trim(), seconds, { ...opts, maxClips });
      setPhase("rendering");
      poll.current = window.setInterval(async () => {
        try {
          const j = await api.job(job_id);
          if (!mounted.current) return;
          setJob(j);
          if (j.state === "succeeded") {
            window.clearInterval(poll.current!); poll.current = null;
            const { candidates } = await api.candidates(pid);
            setCandidates(candidates);
            setSelected(candidates.find((c) => c.name === "enhanced")?.name ?? candidates[0]?.name ?? "enhanced");
            setPhase("review");
          } else if (j.state === "failed") {
            window.clearInterval(poll.current!); poll.current = null;
            setError({ title: "The video couldn't be made",
              body: "Coach couldn't read usable clips in that folder. Your originals are untouched — try a different folder." });
            setPhase("error");
          }
        } catch (e) {
          window.clearInterval(poll.current!); poll.current = null; fail(e);
        }
      }, 1000);
    } catch (e) { fail(e); }
  }

  async function save() {
    const pid = projectId.current;
    if (!pid) return;
    try {
      let dest: string | undefined;
      if (nativePickerAvailable()) dest = (await pickNative("folder")) ?? undefined;
      const r = await api.approve(pid, selected, dest);
      setSavedTo(r.saved_to ?? "kept in this project");
    } catch (e) { fail(e); }
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
        <SectionHeader title="Your video is ready" subtitle="Pick the version you like, then save it." />
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
          </div>
          <div className="stack">
            <div className="card stack">
              <h2>Why Coach chose this</h2>
              <p className="muted small" style={{ margin: 0 }}>{why}</p>
            </div>
            <Button variant="primary" size="lg" icon="check" onClick={save}>Save video</Button>
            {savedTo && (
              <div className="pill ok"><Icon name="check" size={14} /> Saved · {savedTo}</div>
            )}
            <Button icon="plus" onClick={() => { setPhase("form"); setCandidates([]); setSavedTo(null); }}>
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
          <Button variant="primary" size="lg" icon="sparkles" onClick={() => start(true)} disabled={!canCreate}>
            Make my video
          </Button>
          <Button variant="ghost" onClick={() => start(false)} disabled={!canCreate}>
            Review 3 versions instead
          </Button>
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
