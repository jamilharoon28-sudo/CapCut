import { useEffect, useRef, useState } from "react";

import { api, type Candidate } from "../api";
import { Loading, StateCard } from "../components/States";

type Phase = "form" | "rendering" | "review" | "error";

// Automation-first flow (pack docs 15–16): point Coach at a folder of clips for
// ONE video and it renders Clean / Enhanced / Bold candidates you can play — no
// CapCut needed. Your originals are never changed.
export function CreateVideo() {
  const [phase, setPhase] = useState<Phase>("form");
  const [folder, setFolder] = useState("");
  const [seconds, setSeconds] = useState(20);
  const [maxClips, setMaxClips] = useState(8);
  const [mode, setMode] = useState("auto");
  const [musicPath, setMusicPath] = useState("");
  const [logoPath, setLogoPath] = useState("");
  const [captions, setCaptions] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [chosen, setChosen] = useState<string | null>(null);
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
      const { job_id } = await api.autocreate(project.id, folder.trim(), seconds, {
        captions: capLines.length ? capLines : undefined,
        maxClips,
        mode,
        musicPath: musicPath.trim() || undefined,
        logoPath: logoPath.trim() || undefined,
      });
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
          setError("Rendering failed. Check that the folder has video clips Coach can read.");
          setPhase("error");
        }
      }, 1000);
    } catch (e) {
      setError((e as Error).message);
      setPhase("error");
    }
  }

  if (phase === "rendering")
    return (
      <section>
        <h1>Making your video</h1>
        <Loading stage={stage} />
        <p className="muted" style={{ marginTop: 12 }}>
          Coach is rendering three versions locally. This usually takes under a minute for a short
          reel. You can leave this screen — the work keeps going.
        </p>
      </section>
    );

  if (phase === "review")
    return (
      <section>
        <h1>Your edits are ready</h1>
        <p className="muted">
          Play each one and pick a favourite. <strong>Enhanced</strong> is Coach's recommendation.
        </p>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {candidates.map((c) => {
            const selected = chosen === c.name;
            return (
              <figure
                key={c.name}
                className="card"
                style={{
                  margin: 0, width: 260,
                  outline: selected ? "3px solid var(--accent)" : "none",
                  outlineOffset: 2,
                }}
              >
                <video
                  src={c.url}
                  controls
                  playsInline
                  style={{ width: "100%", borderRadius: 12, background: "var(--canvas)",
                           aspectRatio: "9 / 16" }}
                />
                <figcaption style={{ marginTop: 8, display: "flex", justifyContent: "space-between",
                                     alignItems: "center" }}>
                  <span style={{ textTransform: "capitalize", fontWeight: 600 }}>
                    {c.name}
                    {c.name === "enhanced" &&
                      <span className="badge" style={{ marginLeft: 8 }}>Recommended</span>}
                  </span>
                  <button
                    className={selected ? "primary" : ""}
                    style={{ minHeight: 36, padding: "0 12px" }}
                    onClick={() => setChosen(c.name)}
                  >
                    {selected ? "Picked ✓" : "Use this"}
                  </button>
                </figcaption>
              </figure>
            );
          })}
        </div>
        {chosen && (
          <p className="muted" style={{ marginTop: 16 }}>
            Saved on your Mac under <code>~/Library/Application Support/CapCut Coach</code>. You can
            open your pick in CapCut Free for final touches, or share the MP4 as-is.
          </p>
        )}
        <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
          <button onClick={() => { setPhase("form"); setCandidates([]); setChosen(null); }}>
            Make another
          </button>
        </div>
      </section>
    );

  return (
    <section>
      <h1>Create a video</h1>
      <p className="muted">
        Coach turns the clips for <strong>one</strong> video into three finished vertical edits.
        Your originals are never changed, and this works without CapCut.
      </p>
      {error && (
        <div style={{ marginBottom: 12 }}>
          <StateCard icon="⚠️" tone="danger" title="Couldn't start" detail={error} />
        </div>
      )}
      <div className="card" style={{ display: "grid", gap: 18, maxWidth: 560 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Folder with this video's clips</span>
          <input
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            placeholder="/Users/you/Movies/project-raw-footage"
            style={{ minHeight: 44, borderRadius: 12, border: "1px solid var(--hairline)",
                     padding: "0 12px" }}
          />
          <span className="muted" style={{ fontSize: 13 }}>
            In Finder, right-click the folder → <strong>Copy as Pathname</strong>, then paste here.
            Use a folder for one video — not your whole Downloads.
          </span>
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>What kind of video is this?</span>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            style={{ minHeight: 44, borderRadius: 12, border: "1px solid var(--hairline)",
                     padding: "0 12px", font: "inherit", background: "var(--surface)" }}
          >
            <option value="auto">Let Coach decide (recommended)</option>
            <option value="montage">Montage / B-roll (no talking)</option>
            <option value="talking">Talking to camera (cut by speech)</option>
          </select>
          <span className="muted" style={{ fontSize: 13 }}>
            Talking mode keeps your best takes and cuts the “ums” — it needs the one-time
            speech setup (<code>scripts/setup-whisper.sh</code>).
          </span>
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Target length: {seconds}s</span>
          <input type="range" min={8} max={60} value={seconds}
                 onChange={(e) => setSeconds(Number(e.target.value))} />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Most shots to include: {maxClips}</span>
          <input type="range" min={3} max={16} value={maxClips}
                 onChange={(e) => setMaxClips(Number(e.target.value))} />
          <span className="muted" style={{ fontSize: 13 }}>
            Fewer shots = each stays on screen longer.
          </span>
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Music track (optional — enables beat-synced cuts)</span>
          <input
            value={musicPath}
            onChange={(e) => setMusicPath(e.target.value)}
            placeholder="/Users/you/Music/track.mp3"
            style={{ minHeight: 44, borderRadius: 12, border: "1px solid var(--hairline)",
                     padding: "0 12px" }}
          />
          <span className="muted" style={{ fontSize: 13 }}>
            With music, Coach cuts on the beat (~2s phrases) and uses it as the soundtrack.
            Use a track you own or that's licensed.
          </span>
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Logo image (optional — adds a branded outro)</span>
          <input
            value={logoPath}
            onChange={(e) => setLogoPath(e.target.value)}
            placeholder="/Users/you/Brand/logo.png"
            style={{ minHeight: 44, borderRadius: 12, border: "1px solid var(--hairline)",
                     padding: "0 12px" }}
          />
        </label>
        <label style={{ display: "grid", gap: 6 }}>
          <span>On-screen text (optional — one line per shot, your campaign copy)</span>
          <textarea
            value={captions}
            onChange={(e) => setCaptions(e.target.value)}
            rows={3}
            placeholder={"Struggling with dry skin?\nStep one: cleanse\nBook today"}
            style={{ borderRadius: 12, border: "1px solid var(--hairline)", padding: 10,
                     font: "inherit" }}
          />
        </label>
        <div>
          <button className="primary" onClick={start}>Create my videos</button>
        </div>
      </div>
    </section>
  );
}
