// The truthful workflow: Coach renders the finished MP4 itself, so the old
// "Finish in CapCut" step is gone (pack docs 15–20; CapCut is optional).
const STEPS = ["Sources", "Coach Edit", "Render", "Review & Learn"];
const STEP_KEYS = ["sources", "edit", "render", "review"];

export function ProjectPath({ current }: { current: string }) {
  const idx = Math.max(0, STEP_KEYS.indexOf(current));
  return (
    <ol className="row" aria-label="Project steps" style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {STEPS.map((label, i) => {
        const state = i < idx ? "done" : i === idx ? "current" : "todo";
        return (
          <li key={label} aria-current={state === "current" ? "step" : undefined}
            className={`pill ${state === "todo" ? "neutral" : state === "done" ? "ok" : ""}`}>
            {state === "done" ? "✓ " : `${i + 1} `}{label}
          </li>
        );
      })}
    </ol>
  );
}
