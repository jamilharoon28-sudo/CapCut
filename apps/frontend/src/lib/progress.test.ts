import { describe, expect, it } from "vitest";

import { FRIENDLY_STAGES, mapJobToProgress } from "./progress";

const job = (o: Partial<import("../api").Job>) =>
  ({ id: "j", state: "running", stage: null, percent: null, ...o });

describe("mapJobToProgress", () => {
  it("shows indeterminate while running without granular percent", () => {
    const v = mapJobToProgress(job({ state: "running", stage: "rendering" }));
    expect(v.indeterminate).toBe(true);
    expect(v.percent).toBeNull();
    expect(v.done).toBe(false);
  });

  it("marks the rendering stage current and earlier stages done", () => {
    const v = mapJobToProgress(job({ state: "running", stage: "rendering" }));
    const rendering = v.steps.find((s) => s.label === "Rendering");
    expect(rendering?.state).toBe("current");
    expect(v.steps[0].state).toBe("done");
  });

  it("completes all stages on success with 100%", () => {
    const v = mapJobToProgress(job({ state: "succeeded", stage: "done", percent: 100 }));
    expect(v.done).toBe(true);
    expect(v.percent).toBe(100);
    expect(v.steps.every((s) => s.state === "done")).toBe(true);
    expect(v.steps).toHaveLength(FRIENDLY_STAGES.length);
  });

  it("flags failure without pretending progress", () => {
    const v = mapJobToProgress(job({ state: "failed", stage: "render_error" }));
    expect(v.failed).toBe(true);
    expect(v.caption).toMatch(/went wrong/);
  });
});
