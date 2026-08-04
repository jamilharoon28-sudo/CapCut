// Map the real backend job to calm, friendly progress. Never invents a
// percentage: when the backend doesn't report granular percent, we show an
// indeterminate bar (honest) rather than a fake number.
import type { Job } from "../api";
import type { StepState } from "../components/ui";

export const FRIENDLY_STAGES = [
  "Checking footage",
  "Finding the strongest moments",
  "Building the story",
  "Adding captions & audio",
  "Rendering",
  "Quality check",
] as const;

// Backend stage string → index into FRIENDLY_STAGES.
const STAGE_INDEX: Record<string, number> = {
  queued: 0,
  rendering: 4,
  render_error: 4,
  done: FRIENDLY_STAGES.length,
};

export type ProgressView = {
  steps: { label: string; state: StepState }[];
  indeterminate: boolean;
  percent: number | null;
  caption: string;
  done: boolean;
  failed: boolean;
};

export function mapJobToProgress(job: Job | null): ProgressView {
  const state = job?.state ?? "queued";
  const succeeded = state === "succeeded";
  const failed = state === "failed";
  let current = succeeded ? FRIENDLY_STAGES.length : STAGE_INDEX[job?.stage ?? "queued"] ?? 0;
  if (failed) current = STAGE_INDEX[job?.stage ?? "rendering"] ?? 4;

  const steps = FRIENDLY_STAGES.map((label, i) => ({
    label,
    state: (succeeded || i < current ? "done" : i === current ? "current" : "pending") as StepState,
  }));

  // The backend only reports a coarse percent (start/done), so treat anything
  // between as indeterminate rather than pretending precision.
  const p = job?.percent ?? null;
  const meaningful = typeof p === "number" && p > 5 && p < 100;
  return {
    steps,
    indeterminate: !succeeded && !meaningful && !failed,
    percent: succeeded ? 100 : meaningful ? p : null,
    caption: succeeded
      ? "Done — your video is ready."
      : failed
        ? "Something went wrong while making the video."
        : "Coach is making your video. This stays on your Mac — you can leave this screen.",
    done: succeeded,
    failed,
  };
}
