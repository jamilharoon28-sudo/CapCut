import { useEffect, useState } from "react";

import { api, type Project } from "./api";
import { ProjectPath } from "./components/ProjectPath";
import { Loading, StateCard } from "./components/States";
import { CreateVideo } from "./screens/CreateVideo";

const DESTINATIONS = ["Home", "Create", "Projects", "Learn My Style", "Connections", "Settings"] as const;
type Destination = (typeof DESTINATIONS)[number];

export default function App() {
  const [dest, setDest] = useState<Destination>("Home");
  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", minHeight: "100vh" }}>
      <nav
        aria-label="Primary"
        style={{
          borderRight: "1px solid var(--hairline)",
          padding: 16,
          background: "var(--surface)",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 18, padding: "8px 12px 20px" }}>CapCut Coach</div>
        {DESTINATIONS.map((d) => (
          <button
            key={d}
            onClick={() => setDest(d)}
            aria-current={dest === d ? "page" : undefined}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              marginBottom: 6,
              border: "none",
              background: dest === d ? "#efe9ff" : "transparent",
              color: dest === d ? "var(--accent-hover)" : "var(--text)",
              fontWeight: dest === d ? 600 : 400,
            }}
          >
            {d}
          </button>
        ))}
      </nav>
      <main style={{ padding: 32, maxWidth: 880 }}>
        {dest === "Home" && <Home onOpenProjects={() => setDest("Create")} />}
        {dest === "Create" && <CreateVideo />}
        {dest === "Projects" && <Projects />}
        {dest === "Learn My Style" && <LearnMyStyle />}
        {dest === "Connections" && <Connections />}
        {dest === "Settings" && <Settings />}
      </main>
    </div>
  );
}

function Home({ onOpenProjects }: { onOpenProjects: () => void }) {
  return (
    <section>
      <h1>Make a video</h1>
      <p className="muted">
        Add footage or a finished example. Coach prepares a first cut, then guides you through
        finishing it in CapCut. Your originals are never changed.
      </p>
      <div className="card" style={{ marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Create a video</h2>
        <p className="muted">Start from a script, raw footage, or both.</p>
        <button className="primary" onClick={onOpenProjects}>
          Create a video
        </button>
      </div>
      <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
        {["Learn from finished videos", "Continue a project", "Review an export"].map((t) => (
          <div key={t} className="card" style={{ flex: "1 1 220px" }}>
            <strong>{t}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function Projects() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function load() {
    try {
      setProjects((await api.listProjects()).projects);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, []);

  async function create() {
    setCreating(true);
    try {
      await api.createProject("Untitled video");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCreating(false);
    }
  }

  if (error)
    return (
      <StateCard
        icon="🔌"
        tone="warning"
        title="Can't reach Coach yet"
        detail={error}
        action={<button onClick={() => location.reload()}>Try again</button>}
      />
    );
  if (!projects) return <Loading stage="Loading your projects…" />;

  return (
    <section>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Projects</h1>
        <button className="primary" onClick={create} disabled={creating}>
          {creating ? "Creating…" : "New project"}
        </button>
      </div>
      {projects.length === 0 ? (
        <StateCard
          icon="🎬"
          title="No projects yet"
          detail="Create your first project to prepare an edit."
          action={<button className="primary" onClick={create}>Create a video</button>}
        />
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 12 }}>
          {projects.map((p) => (
            <li key={p.id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{p.title}</strong>
                <span className="badge">{p.status}</span>
              </div>
              <div style={{ marginTop: 12 }}>
                <ProjectPath current={p.step} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function LearnMyStyle() {
  return (
    <section>
      <h1>Learn my style</h1>
      <StateCard
        icon="🧠"
        tone="warning"
        title="Needs 15–20 paired examples"
        detail="Add matched raw footage and the approved finished video for each example. Coach learns one universal style. This step is available once you add examples on your Mac."
      />
    </section>
  );
}

function Connections() {
  return (
    <section>
      <h1>Connections</h1>
      <p className="muted">
        Choose the folders Coach may read. CapCut Cloud and Google Drive are always{" "}
        <strong>read-only</strong> — Coach never deletes cloud files.
      </p>
      <div className="card" style={{ marginTop: 16 }}>
        <strong>Google Drive & CapCut Cloud</strong>
        <span className="badge blocked" style={{ marginLeft: 8 }}>
          read-only
        </span>
        <p className="muted" style={{ marginBottom: 0 }}>
          Only the folders you pick are indexed. Nothing in the cloud is ever moved or removed.
        </p>
      </div>
    </section>
  );
}

function Settings() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [doctor, setDoctor] = useState<Awaited<ReturnType<typeof api.doctor>> | null>(null);
  useEffect(() => {
    void api.status().then(setStatus).catch(() => setStatus({}));
    void api.doctor().then(setDoctor).catch(() => setDoctor(null));
  }, []);
  return (
    <section>
      <h1>Settings</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>System check</h2>
        {!doctor ? (
          <Loading stage="Checking your Mac…" />
        ) : (
          <ul style={{ paddingLeft: 18 }}>
            {Object.entries(doctor.checks).map(([name, c]) => (
              <li key={name}>
                {name}: <strong>{c.ok ? "ok" : "needs attention"}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Safety</h2>
        <p className="muted" style={{ marginBottom: 0 }}>
          Direct CapCut writes:{" "}
          <strong>{status?.direct_capcut_write_enabled ? "enabled" : "off (safe handoff)"}</strong>.
          Extra paid Claude usage:{" "}
          <strong>{status?.claude_paid_overage_enabled ? "on" : "off"}</strong>.
        </p>
      </div>
    </section>
  );
}
