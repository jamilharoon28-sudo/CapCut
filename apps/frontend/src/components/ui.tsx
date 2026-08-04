import type { ButtonHTMLAttributes, ReactNode } from "react";

// ---------- Icon (inline SVG, no emoji, no dependency) ----------
export type IconName =
  | "home" | "folder" | "sparkles" | "link" | "gear" | "video" | "film" | "text"
  | "image" | "music" | "check" | "alert" | "info" | "lock" | "play" | "plus"
  | "scissors" | "wand" | "reveal" | "chevron";

const PATHS: Record<IconName, ReactNode> = {
  home: <path d="M3 10.5 12 3l9 7.5M5 9.5V20h14V9.5" />,
  folder: <path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2h8.5A1.5 1.5 0 0 1 21 8.5V18a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z" />,
  sparkles: <path d="M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8zM18 14l.9 2.1L21 17l-2.1.9L18 20l-.9-2.1L15 17l2.1-.9z" />,
  link: <path d="M9 15l6-6M8 12H6a3 3 0 0 1 0-6h3M16 12h2a3 3 0 0 1 0 6h-3" />,
  gear: <><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" /></>,
  video: <><rect x="3" y="6" width="13" height="12" rx="2" /><path d="M16 10l5-3v10l-5-3" /></>,
  film: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4" /></>,
  text: <path d="M4 6h16M4 12h16M4 18h10" />,
  image: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="M4 17l5-4 4 3 3-2 4 3" /></>,
  music: <><path d="M9 18V6l10-2v12" /><circle cx="6.5" cy="18" r="2.5" /><circle cx="16.5" cy="16" r="2.5" /></>,
  check: <path d="M4 12.5l5 5 11-11" />,
  alert: <><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
  lock: <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  play: <path d="M8 5l11 7-11 7z" />,
  plus: <path d="M12 5v14M5 12h14" />,
  scissors: <><circle cx="6" cy="6" r="2.5" /><circle cx="6" cy="18" r="2.5" /><path d="M8 8l12 10M8 16L20 6" /></>,
  wand: <path d="M15 4l1 2 2 1-2 1-1 2-1-2-2-1 2-1zM4 20l8-8" />,
  reveal: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 9h18" /></>,
  chevron: <path d="M9 6l6 6-6 6" />,
};

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      {PATHS[name]}
    </svg>
  );
}

// ---------- Button ----------
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "ghost";
  size?: "md" | "lg";
  icon?: IconName;
};
export function Button({ variant = "default", size = "md", icon, children, className = "", ...rest }: ButtonProps) {
  const cls = ["btn",
    variant === "primary" ? "btn-primary" : variant === "ghost" ? "btn-ghost" : "",
    size === "lg" ? "btn-lg" : "", className].filter(Boolean).join(" ");
  return (
    <button className={cls} {...rest}>
      {icon && <Icon name={icon} size={size === "lg" ? 20 : 18} />}
      {children}
    </button>
  );
}

// ---------- StatusPill ----------
export function StatusPill({ tone = "neutral", children }:
  { tone?: "brand" | "ok" | "warn" | "bad" | "neutral"; children: ReactNode }) {
  const map = { brand: "", ok: "ok", warn: "warn", bad: "bad", neutral: "neutral" } as const;
  return <span className={`pill ${map[tone]}`}>{children}</span>;
}

// ---------- SectionHeader ----------
export function SectionHeader({ title, subtitle, action }:
  { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="section-h">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ---------- SourceCard ----------
export function SourceCard({ icon, title, required, value, hint, action }:
  { icon: IconName; title: string; required?: boolean; value?: string | null;
    hint?: ReactNode; action: ReactNode }) {
  return (
    <div className="source">
      <div className="ico"><Icon name={icon} /></div>
      <div className="grow">
        <div className="between">
          <h3>{title}{required && <span className="req-star" aria-label="required"> *</span>}</h3>
          {action}
        </div>
        {value ? <div className="path" title={value}>{value}</div>
               : hint && <div className="small muted" style={{ marginTop: 4 }}>{hint}</div>}
      </div>
    </div>
  );
}

// ---------- EmptyState ----------
export function EmptyState({ icon, title, body, action }:
  { icon: IconName; title: string; body?: ReactNode; action?: ReactNode }) {
  return (
    <div className="card empty">
      <div className="ico"><Icon name={icon} size={26} /></div>
      <h2>{title}</h2>
      {body && <p className="muted">{body}</p>}
      {action}
    </div>
  );
}

// ---------- ProgressSteps ----------
export type StepState = "done" | "current" | "pending";
export function ProgressSteps({ steps }: { steps: { label: string; state: StepState }[] }) {
  return (
    <ol className="steps">
      {steps.map((s, i) => (
        <li key={s.label} className={`step ${s.state}`} aria-current={s.state === "current" ? "step" : undefined}>
          <span className="bullet">{s.state === "done" ? <Icon name="check" size={14} /> : i + 1}</span>
          {s.label}
        </li>
      ))}
    </ol>
  );
}
