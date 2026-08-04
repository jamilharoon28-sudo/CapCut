import { useEffect, useRef, useState } from "react";

import { api, type Candidate } from "../api";
import { Loading, StateCard } from "../components/States";

type Phase = "form" | "rendering" | "review" | "error";

// Automation-first flow (pack docs 15–16): point Coach at a folder of clips and
// it renders Clean / Enhanced / Bold candidates you can play — no CapCut needed.
export function CreateVideo() {
  const [phase, setPhase] = useState<Phase>("form");
  const [folder, setFolder] = useState("");
  const [seconds, setSeconds] = useState(20);
  const [captions, setCaptions] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState("Starting…");
  const pollRef = useRef<number | null>(null);

  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  async function start() {
    setError(null);
    if (!folder.trim()) { setError("Paste the full path to a folder of video clips."); return; }
    try {
      const project = await api.createProject("New video");
      const capLines = captions.split("\n").map((s) => s.trim()).filter(Boolean);
      const { job_id } = await api.autocreate(
        project.id, folder.trim(), seconds, capLines.length ? capLines : undefined,
      );
      setPhase("rendering");
      setStage("Coach is building three edits…");
      pollRef.current = window.setInterval(async () => {
        const job = await api.job(job_id);
        setStage(job.stage === "rendering" ? "Rendering your candidates…" : job.stage ?? "Working…");
        if (job.state === "succeeded") {
          window.clearInterval(pollRef.current!);
          const { candidates } = await api.candidates(project.id);
          setCandidates(candidates);
          setPhase("review");
        } else if (job.state === "failed") {
          window.clearInterval(pollRef.current!);
          setError("Rendering failed. Check that the folder has video clips and FFmpeg is installed.");
          setPhase("error");
        }
      }, 1000);
    } catch (e) {
      setError((e as Error).message);
      setPhase("error");
    }
  }

  if (phase === "rendering") return <Loading stage={stage} />;

  if (phase === "review")
    return (
      <section>
        <h1>Your edits are ready</h1>
        <p className="muted">Play each one. Pick a favourite — Coach learns from your choice.</p>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {candidates.map((c) => (
            <figure key={c.name} className="card" style={{ margin: 0, width: 260 }}>
              <video
                src={c.url}
                controls
                playsInline
                style={{ width: "100%", borderRadius: 12, background: "var(--canvas)", aspectRatio: "9 / 16" }}
              />
              <figcaption style={{ marginTop: 8, textTransform: "capitalize", fontWeight: 600 }}>
                {c.name}
                {c.name === "enhanced" && <span className="badge" style={{ marginLeft: 8 }}>Recommended</span>}
              </figcaption>
            </figure>
          ))}
        </div>
        <div style={{ marginTop: 20 }}>
          <button onClick={() => { setPhase("form"); setCandidates([]); }}>Make another</button>
        </div>
      </section>
    );

  return (
    <section>
      <h1>Create a video</h1>
      <p className="muted">
        Coach turns a folder of raw clips into three finished vertical videos. Your originals are
        never changed, and this works without CapCut.
      </p>
      {error && (
        <div style={{ marginBottom: 12 }}>
          <StateCard icon="⚠️" tone="danger" title="Couldn't start" detail={error} />
        </div>
      )}
      <div className="card" style={{ display: "grid", gap: 16, maxWidth: 560 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Folder of video clips</span>
          <input
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            placeholder="/Users/you/Movies/raw-footage"
            style={{ minHeight: 44, borderRadius: 12, border: "1px solid var(--hairline)", padding: "0 12px" }}
          />
          <span className="muted" style={{ fontSize: 13 }}>
            Tip: in Finder, right-click the folder → Copy as Pathname, then paste here.
          </span>
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Target length: {seconds}s</span>
          <input type="range" min={8} max={60} value={seconds}
                 onChange={(e) => setSeconds(Number(e.target.value))} />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>On-screen captions (optional — one line per shot)</span>
          <textarea
            value={captions}
            onChange={(e) => setCaptions(e.target.value)}
            rows={3}
            placeholder={"Struggling with dry skin?\nStep one: cleanse\nBook today"}
            style={{ borderRadius: 12, border: "1px solid var(--hairline)", padding: 10, font: "inherit" }}
          />
        </label>
        <div>
          <button className="primary" onClick={start}>Create my videos</button>
        </div>
      </div>
    </section>
  );
}
