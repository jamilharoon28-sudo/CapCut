import { Icon, SectionHeader, StatusPill } from "../components/ui";

// Only real connection states. Google Drive and CapCut handoff are not
// implemented, so they're shown as clearly unavailable — never as working.
export function Connections() {
  return (
    <div className="container">
      <SectionHeader title="Connections" subtitle="Where Coach reads from. Everything stays on your Mac." />
      <div className="stack">
        <div className="card">
          <div className="between">
            <div className="row"><Icon name="folder" /> <strong>Local footage folders</strong></div>
            <StatusPill tone="ok">Available</StatusPill>
          </div>
          <p className="small muted" style={{ margin: "8px 0 0" }}>
            You choose a folder each time you make a video. Coach reads those clips and never changes them.
          </p>
        </div>

        <div className="card">
          <div className="between">
            <div className="row"><Icon name="music" /> <strong>Approved music folder</strong></div>
            <StatusPill tone="neutral">Optional</StatusPill>
          </div>
          <p className="small muted" style={{ margin: "8px 0 0" }}>
            Point Coach at a folder of tracks you own or have licensed and it can pick one automatically.
            It only reads local files — it never searches the internet for music.
          </p>
        </div>

        <div className="card" style={{ opacity: 0.7 }}>
          <div className="between">
            <div className="row"><Icon name="link" /> <strong>Google Drive</strong></div>
            <StatusPill tone="neutral">Not available yet</StatusPill>
          </div>
          <p className="small muted" style={{ margin: "8px 0 0" }}>
            Cloud sources aren’t connected. If added later, any cloud folder would be read-only —
            Coach would never move, delete or reorganise your cloud files.
          </p>
        </div>

        <div className="card" style={{ opacity: 0.7 }}>
          <div className="between">
            <div className="row"><Icon name="video" /> <strong>CapCut</strong></div>
            <StatusPill tone="neutral">Optional, later</StatusPill>
          </div>
          <p className="small muted" style={{ margin: "8px 0 0" }}>
            Coach already renders a finished MP4, so CapCut isn’t required. An optional “open in
            CapCut” hand-off may be added later; it would never write to CapCut’s internal files.
          </p>
        </div>
      </div>
    </div>
  );
}
