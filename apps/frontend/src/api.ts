// Local API client. Loopback + bearer token (unchanged security posture). Errors
// carry a friendly message for the UI while keeping the stable code for logs.

export type Project = {
  id: string; title: string; step: string; status: string; style_dna_version: string | null;
};
export type DoctorCheck = { ok: boolean; detail?: string; [k: string]: unknown };
export type Candidate = { name: string; file: string; ok: boolean; url: string; detail: string;
  qc?: { code: string; severity: string; message: string }[] };
export type Job = { id: string; state: string; stage: string | null; percent: number | null };
export type Request = {
  type: string; what_needed: string; why: string; recommended_action: string;
  fallback: string; quality_impact: string; blocking: boolean; recording_direction: string | null;
};
export type Readiness = {
  status: "READY" | "READY_WITH_SUGGESTIONS" | "NEEDS_HELP"; headline: string;
  required_resolved: number; required_total: number;
  blocking_requests: Request[]; suggestions: Request[];
};

export class CoachError extends Error {
  code: string;
  constructor(code: string, message: string) { super(message); this.code = code; }
}

function token(): string {
  const w = window as unknown as { __COACH_TOKEN__?: string };
  return w.__COACH_TOKEN__ ?? localStorage.getItem("coach_token") ?? "";
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token()}`,
        ...(init.headers ?? {}) },
    });
  } catch {
    throw new CoachError("backend_unavailable",
      "Coach isn't running. Reopen the app, or wait a moment and try again.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body?.error ?? {}) as { code?: string; message?: string };
    throw new CoachError(detail.code ?? `http_${res.status}`,
      detail.message ?? "Something went wrong. Please try again.");
  }
  return (await res.json()) as T;
}

type AutoOpts = { captions?: string[]; maxClips?: number; mode?: string;
  musicPath?: string; logoPath?: string };

export const api = {
  status: () => req<Record<string, unknown>>("/system/status"),
  doctor: () => req<{ checks: Record<string, DoctorCheck>; macos_only_checks_blocked: boolean }>(
    "/system/doctor", { method: "POST" }),
  storage: () => req<Record<string, number>>("/system/storage"),
  cacheSize: () => req<{ bytes: number }>("/system/cache/size"),
  cacheCleanup: () => req<{ freed_bytes: number }>("/system/cache/cleanup",
    { method: "POST", body: JSON.stringify({ confirm: true }) }),

  listProjects: () => req<{ projects: Project[] }>("/projects"),
  createProject: (title: string) =>
    req<Project>("/projects", { method: "POST", body: JSON.stringify({ title }) }),

  preflight: (pid: string, mediaDir: string, opts?: AutoOpts) =>
    req<Readiness>(`/projects/${pid}/preflight`, {
      method: "POST",
      body: JSON.stringify({ media_dir: mediaDir, captions: opts?.captions,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null }),
    }),

  autocreate: (pid: string, mediaDir: string, targetSeconds: number, opts?: AutoOpts) =>
    req<{ job_id: string }>(`/projects/${pid}/autocreate`, {
      method: "POST",
      body: JSON.stringify({ media_dir: mediaDir, target_seconds: targetSeconds,
        captions: opts?.captions, max_clips: opts?.maxClips, mode: opts?.mode,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null }),
    }),

  makeMyVideo: (pid: string, mediaDir: string, targetSeconds: number, opts?: AutoOpts) =>
    req<{ job_id: string }>(`/projects/${pid}/make-my-video`, {
      method: "POST",
      body: JSON.stringify({ media_dir: mediaDir, target_seconds: targetSeconds,
        captions: opts?.captions, mode: opts?.mode,
        music_path: opts?.musicPath || null, logo_path: opts?.logoPath || null }),
    }),

  job: (id: string) => req<Job>(`/jobs/${id}`),
  candidates: (pid: string) => req<{ candidates: Candidate[] }>(`/projects/${pid}/candidates`),
  approve: (pid: string, candidate: string, destinationDir?: string) =>
    req<{ approved: string; saved_to: string | null }>(`/projects/${pid}/approve`, {
      method: "POST",
      body: JSON.stringify({ candidate, destination_dir: destinationDir || null }),
    }),
};
