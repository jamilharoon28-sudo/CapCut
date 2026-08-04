import { useEffect, useState } from "react";

import { api, type DoctorCheck, type Trust } from "../api";
import { PathField } from "../components/PathField";
import { Button, Icon, SectionHeader, StatusPill } from "../components/ui";

// Friendly system status. Raw internal keys are translated; cleanup touches only
// Coach's own cache and always asks first.
const FRIENDLY: Record<string, string> = {
  python: "Core engine", ffmpeg: "Video engine", ffprobe: "Media inspector",
  node: "Interface tools", pnpm: "Interface tools", uv: "Setup tools",
  claude_cli: "Optional AI helper", capcut: "CapCut (optional)",
};

function fmtGb(bytes: number) { return `${(bytes / 1e9).toFixed(2)} GB`; }

export function Settings() {
  const [doctor, setDoctor] = useState<Record<string, DoctorCheck> | null>(null);
  const [storage, setStorage] = useState<Record<string, number> | null>(null);
  const [cacheBytes, setCacheBytes] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [freed, setFreed] = useState<number | null>(null);
  const [trust, setTrust] = useState<Trust | null>(null);

  useEffect(() => {
    void api.doctor().then((d) => setDoctor(d.checks)).catch(() => setDoctor({}));
    void api.storage().then(setStorage).catch(() => {});
    void api.cacheSize().then((c) => setCacheBytes(c.bytes)).catch(() => {});
    void Promise.resolve(api.trust?.()).then((t) => t && setTrust(t)).catch(() => {});
  }, []);

  async function setSaveFolder(path: string) {
    try {
      const r = await api.setDefaultOutput(path || null);
      setTrust((t) => (t ? { ...t, default_output_dir: r.default_output_dir,
        ready_for_one_tap: t.autopilot_unlocked && !!r.default_output_dir } : t));
    } catch { /* surfaced via the field staying unset */ }
  }

  // "Ready" means the essential local engines are present. Optional tools
  // (CapCut, Claude helper, Node/pnpm/uv) don't block making a video.
  const ESSENTIAL = ["python", "ffmpeg", "ffprobe"];
  const ready = doctor ? ESSENTIAL.every((k) => doctor[k]?.ok) : false;

  async function cleanup() {
    const r = await api.cacheCleanup();
    setFreed(r.freed_bytes); setConfirming(false);
    setCacheBytes((b) => (b === null ? null : Math.max(0, b - r.freed_bytes)));
  }

  return (
    <div className="container">
      <SectionHeader title="Settings" subtitle="Everything runs locally and privately." />
      <div className="stack">
        <div className="card">
          <div className="between">
            <div className="row"><Icon name={ready ? "check" : "alert"} /> <strong>System</strong></div>
            <StatusPill tone={ready ? "ok" : "warn"}>{ready ? "Ready" : "Needs attention"}</StatusPill>
          </div>
          {doctor && (
            <ul className="small" style={{ margin: "10px 0 0", paddingLeft: 0, listStyle: "none" }}>
              {Object.entries(doctor).filter(([k]) => k in FRIENDLY).map(([k, c]) => (
                <li key={k} className="between" style={{ padding: "4px 0" }}>
                  <span>{FRIENDLY[k]}</span>
                  <StatusPill tone={c.ok ? "ok" : k === "capcut" || k === "claude_cli" ? "neutral" : "warn"}>
                    {c.ok ? "OK" : "Set up"}
                  </StatusPill>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="between"><strong>Storage</strong>
            {storage && <span className="muted small">{storage.free_gb} GB free of {storage.total_gb} GB</span>}
          </div>
          <div className="divider" />
          <div className="between">
            <div>
              <strong>Temporary files</strong>
              <div className="small muted">
                {cacheBytes !== null ? `${fmtGb(cacheBytes)} of Coach cache can be cleared.` : "Checking…"}
              </div>
            </div>
            {freed !== null ? (
              <StatusPill tone="ok">Freed {fmtGb(freed)}</StatusPill>
            ) : confirming ? (
              <div className="row">
                <Button onClick={() => setConfirming(false)}>Cancel</Button>
                <Button variant="primary" onClick={cleanup}>Clear now</Button>
              </div>
            ) : (
              <Button onClick={() => setConfirming(true)} disabled={!cacheBytes}>Free up space</Button>
            )}
          </div>
          <p className="small muted" style={{ margin: "10px 0 0" }}>
            This removes only Coach’s cache/temporary files. Your videos, projects and originals are never touched.
          </p>
        </div>

        <div className="card stack">
          <div className="between">
            <strong>Automatic saving (one-tap)</strong>
            {trust && (
              <StatusPill tone={trust.ready_for_one_tap ? "ok" : "neutral"}>
                {trust.ready_for_one_tap ? "On" : trust.autopilot_unlocked ? "Set a folder" : "Earning trust"}
              </StatusPill>
            )}
          </div>
          <p className="small muted" style={{ margin: 0 }}>
            {trust && !trust.autopilot_unlocked
              ? `After you approve ${trust.threshold} videos, Coach can make and save a video in one tap. ${trust.approvals}/${trust.threshold} so far.`
              : "Coach can make a video and save a copy to this folder in one tap. It only ever writes here — never to your originals or cloud."}
          </p>
          <PathField icon="folder" title="Save finished videos to" kind="folder"
            value={trust?.default_output_dir ?? ""} onChange={setSaveFolder}
            hint="A local folder. Cloud/synced folders stay read-only." />
        </div>

        <div className="card">
          <strong>Privacy & safety</strong>
          <p className="small muted" style={{ margin: "8px 0 0" }}>
            Video processing happens on this Mac. Coach never modifies your original footage and
            never deletes cloud or CapCut content. Speech captions need a one-time local setup.
          </p>
        </div>
      </div>
    </div>
  );
}
