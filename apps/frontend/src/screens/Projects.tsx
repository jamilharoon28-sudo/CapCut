import { useEffect, useState } from "react";

import { api, type Project } from "../api";
import { ProjectPath } from "../components/ProjectPath";
import { Button, EmptyState, SectionHeader, StatusPill } from "../components/ui";

export function Projects({ onCreate }: { onCreate: () => void }) {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api.listProjects().then((r) => setProjects(r.projects))
      .catch((e) => setError((e as Error).message));
  }, []);

  if (error) return (
    <div className="container">
      <EmptyState icon="alert" title="Couldn't load your projects" body={error}
        action={<Button variant="primary" onClick={() => location.reload()}>Try again</Button>} />
    </div>
  );
  if (!projects) return <div className="container"><div className="card">Loading…</div></div>;

  return (
    <div className="container">
      <SectionHeader title="Projects" subtitle="Your videos and their progress."
        action={<Button variant="primary" icon="plus" onClick={onCreate}>Make a video</Button>} />
      {projects.length === 0 ? (
        <EmptyState icon="film" title="No projects yet"
          body="Create your first video and it will appear here."
          action={<Button variant="primary" icon="plus" onClick={onCreate}>Make a video</Button>} />
      ) : (
        <div className="stack">
          {projects.map((p) => (
            <div className="card proj" key={p.id}>
              <div className="thumb" />
              <div className="grow stack" style={{ gap: 8 }}>
                <div className="between">
                  <strong>{p.title}</strong>
                  <StatusPill tone={p.status === "approved" ? "ok" : "neutral"}>{p.status}</StatusPill>
                </div>
                <ProjectPath current={p.step} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
