import { useEffect, useState } from "react";

import { api, type Project } from "../api";
import { Button, EmptyState, Icon, type IconName, StatusPill } from "../components/ui";

const CAPS: { icon: IconName; label: string }[] = [
  { icon: "film", label: "Chooses footage" },
  { icon: "wand", label: "Builds the edit" },
  { icon: "text", label: "Adds captions" },
  { icon: "video", label: "Renders locally" },
];

export function Home({ onCreate, onOpenProjects }: { onCreate: () => void; onOpenProjects: () => void }) {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [freeGb, setFreeGb] = useState<number | null>(null);

  useEffect(() => {
    void api.listProjects().then((r) => setProjects(r.projects)).catch(() => setProjects([]));
    void api.storage().then((s) => setFreeGb(Number(s.free_gb))).catch(() => {});
  }, []);

  return (
    <div className="container stack">
      <div className="card" style={{ padding: "36px 32px" }}>
        <h1 style={{ fontSize: 30 }}>Turn raw footage into a finished video.</h1>
        <p className="muted" style={{ maxWidth: 620 }}>
          Coach picks the best moments, shapes the story, adds captions and approved music when
          available, and renders a finished vertical video — all on your Mac.
        </p>
        <div className="row" style={{ marginTop: 8 }}>
          <Button variant="primary" size="lg" icon="plus" onClick={onCreate}>Make a video</Button>
        </div>
      </div>

      <div className="card">
        <div className="cap-strip">
          {CAPS.map((c) => (
            <div className="cap" key={c.label}>
              <div className="ico"><Icon name={c.icon} /></div>
              <div><strong>{c.label}</strong></div>
            </div>
          ))}
        </div>
      </div>

      {projects === null ? null : projects.length === 0 ? (
        <EmptyState
          icon="film"
          title="No videos yet"
          body="Make your first one — add a folder of clips and Coach does the rest."
          action={<Button variant="primary" icon="plus" onClick={onCreate}>Make a video</Button>}
        />
      ) : (
        <div className="card">
          <div className="between" style={{ marginBottom: 12 }}>
            <h2>Recent projects</h2>
            <Button variant="ghost" onClick={onOpenProjects}>View all</Button>
          </div>
          <div className="stack">
            {projects.slice(0, 3).map((p) => (
              <div className="proj" key={p.id}>
                <div className="thumb" />
                <div className="grow">
                  <strong>{p.title}</strong>
                  <div className="small muted">{p.step}</div>
                </div>
                <StatusPill tone={p.status === "approved" ? "ok" : "neutral"}>{p.status}</StatusPill>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="privacy-note" style={{ maxWidth: 420 }}>
        <Icon name="lock" size={16} />
        <span>Private on this Mac{freeGb !== null ? ` · ${freeGb} GB free` : ""}. Your originals are never changed.</span>
      </div>
    </div>
  );
}
