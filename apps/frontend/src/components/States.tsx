// Polished, honest UI states (design system §10). No indefinite fake progress.
import type { ReactNode } from "react";

export function StateCard({
  icon,
  title,
  detail,
  action,
  tone = "neutral",
}: {
  icon: string;
  title: string;
  detail?: ReactNode;
  action?: ReactNode;
  tone?: "neutral" | "warning" | "danger" | "success";
}) {
  const color =
    tone === "warning"
      ? "var(--warning)"
      : tone === "danger"
        ? "var(--danger)"
        : tone === "success"
          ? "var(--success)"
          : "var(--text)";
  return (
    <div className="card" role="status" style={{ textAlign: "center" }}>
      <div aria-hidden style={{ fontSize: 34 }}>
        {icon}
      </div>
      <h3 style={{ margin: "8px 0 4px", color }}>{title}</h3>
      {detail && <p className="muted" style={{ margin: "0 0 16px" }}>{detail}</p>}
      {action}
    </div>
  );
}

export function Loading({ stage, done, total }: { stage: string; done?: number; total?: number }) {
  const pct = total ? Math.round(((done ?? 0) / total) * 100) : undefined;
  return (
    <div className="card" role="status" aria-live="polite">
      <p style={{ margin: 0 }}>{stage}</p>
      {pct !== undefined ? (
        <>
          <div
            style={{
              height: 8,
              borderRadius: 999,
              background: "var(--hairline)",
              overflow: "hidden",
              marginTop: 12,
            }}
          >
            <div style={{ width: `${pct}%`, height: "100%", background: "var(--accent)" }} />
          </div>
          <p className="muted" style={{ margin: "8px 0 0", fontSize: 13 }}>
            {done} of {total} • you can safely close the app; work resumes automatically
          </p>
        </>
      ) : (
        <p className="muted" style={{ margin: "8px 0 0", fontSize: 13 }}>
          Working locally on your Mac…
        </p>
      )}
    </div>
  );
}
