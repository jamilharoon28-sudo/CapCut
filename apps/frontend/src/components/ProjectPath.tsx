// The visible five-step project path (design system §3).
const STEPS = ["Sources", "Script & Story", "Coach Edit", "Finish in CapCut", "Review & Learn"];
const STEP_KEYS = ["sources", "script", "edit", "finish", "review"];

export function ProjectPath({ current }: { current: string }) {
  const idx = Math.max(0, STEP_KEYS.indexOf(current));
  return (
    <ol
      aria-label="Project steps"
      style={{ display: "flex", gap: 8, listStyle: "none", padding: 0, flexWrap: "wrap" }}
    >
      {STEPS.map((label, i) => {
        const state = i < idx ? "done" : i === idx ? "current" : "todo";
        return (
          <li
            key={label}
            aria-current={state === "current" ? "step" : undefined}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 12px",
              borderRadius: 999,
              fontSize: 13,
              background: state === "current" ? "#efe9ff" : "transparent",
              color: state === "todo" ? "var(--text-2)" : "var(--text)",
              border: "1px solid var(--hairline)",
            }}
          >
            <span aria-hidden style={{ fontWeight: 600 }}>
              {state === "done" ? "✓" : i + 1}
            </span>
            {label}
          </li>
        );
      })}
    </ol>
  );
}
