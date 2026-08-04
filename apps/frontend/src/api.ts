// Local API client. Every request carries the bearer token the backend wrote to
// its support dir; the native shell injects it via window.__COACH_TOKEN__. In the
// browser recovery fallback the user pastes it once.

export type Project = {
  id: string;
  title: string;
  step: string;
  status: string;
  style_dna_version: string | null;
};

export type DoctorCheck = { ok: boolean; detail?: string; [k: string]: unknown };

function token(): string {
  const w = window as unknown as { __COACH_TOKEN__?: string };
  return w.__COACH_TOKEN__ ?? localStorage.getItem("coach_token") ?? "";
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token()}`,
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export type Candidate = { name: string; file: string; ok: boolean; url: string; detail: string };
export type Job = { id: string; state: string; stage: string | null; percent: number | null };

export const api = {
  status: () => req<Record<string, unknown>>("/system/status"),
  doctor: () => req<{ checks: Record<string, DoctorCheck>; macos_only_checks_blocked: boolean }>(
    "/system/doctor",
    { method: "POST" },
  ),
  storage: () => req<Record<string, number>>("/system/storage"),
  listProjects: () => req<{ projects: Project[] }>("/projects"),
  createProject: (title: string) =>
    req<Project>("/projects", { method: "POST", body: JSON.stringify({ title }) }),
  autocreate: (
    pid: string, mediaDir: string, targetSeconds: number,
    opts?: { captions?: string[]; maxClips?: number; mode?: string;
             musicPath?: string; logoPath?: string },
  ) =>
    req<{ job_id: string }>(`/projects/${pid}/autocreate`, {
      method: "POST",
      body: JSON.stringify({
        media_dir: mediaDir, target_seconds: targetSeconds,
        captions: opts?.captions, max_clips: opts?.maxClips, mode: opts?.mode,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null,
      }),
    }),
  makeMyVideo: (
    pid: string, mediaDir: string, targetSeconds: number,
    opts?: { captions?: string[]; mode?: string; musicPath?: string; logoPath?: string },
  ) =>
    req<{ job_id: string }>(`/projects/${pid}/make-my-video`, {
      method: "POST",
      body: JSON.stringify({
        media_dir: mediaDir, target_seconds: targetSeconds,
        captions: opts?.captions, mode: opts?.mode,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null,
      }),
    }),
  job: (id: string) => req<Job>(`/jobs/${id}`),
  candidates: (pid: string) => req<{ candidates: Candidate[] }>(`/projects/${pid}/candidates`),
  preflight: (
    pid: string, mediaDir: string,
    opts?: { captions?: string[]; targetSeconds?: number; musicPath?: string; logoPath?: string },
  ) =>
    req<Readiness>(`/projects/${pid}/preflight`, {
      method: "POST",
      body: JSON.stringify({
        media_dir: mediaDir, captions: opts?.captions, target_seconds: opts?.targetSeconds,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null,
      }),
    }),
};

export type Request = {
  type: string;
  what_needed: string;
  why: string;
  recommended_action: string;
  fallback: string;
  quality_impact: string;
  blocking: boolean;
  recording_direction: string | null;
};
export type Readiness = {
  status: "READY" | "READY_WITH_SUGGESTIONS" | "NEEDS_HELP";
  headline: string;
  required_resolved: number;
  required_total: number;
  blocking_requests: Request[];
  suggestions: Request[];
};
