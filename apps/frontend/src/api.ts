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
};
