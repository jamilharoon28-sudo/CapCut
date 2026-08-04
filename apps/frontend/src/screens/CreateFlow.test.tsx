import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api", () => {
  class CoachError extends Error { code: string; constructor(c: string, m: string) { super(m); this.code = c; } }
  return {
    CoachError,
    api: {
      createProject: vi.fn().mockResolvedValue({ id: "p1", title: "New video", step: "sources", status: "new", style_dna_version: null }),
      preflight: vi.fn(),
      makeMyVideo: vi.fn(),
      autocreate: vi.fn(),
      job: vi.fn(),
      candidates: vi.fn(),
      approve: vi.fn(),
      slots: vi.fn().mockResolvedValue({ slots: [] }),
      review: vi.fn().mockResolvedValue({ groups: [], required_ack_ids: [] }),
      replaceSlot: vi.fn().mockResolvedValue({ job_id: "j2" }),
      trust: vi.fn().mockResolvedValue({ approvals: 0, threshold: 5, remaining: 5,
        autopilot_unlocked: false, default_output_dir: null, ready_for_one_tap: false }),
    },
  };
});

function twoCandidates() {
  (api.makeMyVideo as ReturnType<typeof vi.fn>).mockResolvedValue({ job_id: "j1", auto_save: false });
  (api.job as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "j1", state: "succeeded", stage: "done", percent: 100 });
  (api.candidates as ReturnType<typeof vi.fn>).mockResolvedValue({ candidates: [
    { name: "clean", file: "clean.mp4", ok: true, url: "/previews/p1/clean.mp4", detail: "ok" },
    { name: "enhanced", file: "enhanced.mp4", ok: true, url: "/previews/p1/enhanced.mp4", detail: "ok" },
  ] });
}

import { api } from "../api";
import { CreateFlow } from "./CreateFlow";

beforeEach(() => vi.clearAllMocks());

function typeFolder() {
  const input = screen.getByLabelText(/Raw footage path/);
  fireEvent.change(input, { target: { value: "/Users/me/Movies/raw" } });
}

describe("CreateFlow", () => {
  it("keeps the primary action disabled until footage is provided", () => {
    render(<CreateFlow onDone={() => {}} />);
    expect((screen.getByRole("button", { name: /Make my video/ }) as HTMLButtonElement).disabled).toBe(true);
    typeFolder();
    expect((screen.getByRole("button", { name: /Make my video/ }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("renders Smart Check with Needed and Suggestions in plain language", async () => {
    (api.preflight as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: "READY_WITH_SUGGESTIONS", headline: "Ready — a couple of things would make it better",
      required_resolved: 1, required_total: 1,
      blocking_requests: [],
      suggestions: [{ type: "missing_logo", what_needed: "A transparent logo image.",
        why: "A branded ending matches your style.", recommended_action: "Add your logo.",
        fallback: "Coach ends with a text card.", quality_impact: "Ending is generic.",
        blocking: false, recording_direction: null }],
    });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    fireEvent.click(screen.getByRole("button", { name: /Smart Check/ }));
    await waitFor(() => expect(screen.getByText(/would make it better/)).toBeTruthy());
    expect(screen.getByText(/Suggestions/)).toBeTruthy();
    expect(screen.getByText(/A transparent logo image/)).toBeTruthy();
  });

  it("runs the real job to review and lets the user pick a candidate", async () => {
    (api.makeMyVideo as ReturnType<typeof vi.fn>).mockResolvedValue({ job_id: "j1" });
    (api.job as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "j1", state: "succeeded", stage: "done", percent: 100 });
    (api.candidates as ReturnType<typeof vi.fn>).mockResolvedValue({ candidates: [
      { name: "clean", file: "clean.mp4", ok: true, url: "/previews/p1/candidates/clean.mp4", detail: "ok" },
      { name: "enhanced", file: "enhanced.mp4", ok: true, url: "/previews/p1/candidates/enhanced.mp4", detail: "ok" },
    ] });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    fireEvent.click(screen.getByRole("button", { name: /Make my video/ }));
    await waitFor(() => expect(screen.getByText(/Your video is ready/)).toBeTruthy(), { timeout: 4000 });
    // Enhanced is preselected as the recommendation.
    expect(screen.getByText(/Enhanced is Coach's pick/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /^clean/i }));
    expect(screen.getByText(/most conservative/)).toBeTruthy();
  });

  it("shows a safe, plain-language error when the render fails", async () => {
    (api.makeMyVideo as ReturnType<typeof vi.fn>).mockResolvedValue({ job_id: "j1" });
    (api.job as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "j1", state: "failed", stage: "render_error", percent: null });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    fireEvent.click(screen.getByRole("button", { name: /Make my video/ }));
    await waitFor(() => expect(screen.getByText(/couldn’t be made|couldn't be made/)).toBeTruthy(), { timeout: 4000 });
    expect(screen.getByText(/original footage is safe/)).toBeTruthy();
  });

  it("lets the user swap a clip for an alternative (increment #2)", async () => {
    twoCandidates();
    (api.slots as ReturnType<typeof vi.fn>).mockResolvedValue({ slots: [
      { index: 0, segment_id: "s0", asset_id: "a0", label: "clip 0", timeline_start_us: 0,
        duration_us: 2000000, role: "hook", caption: "Hello", alternatives: [
          { asset_id: "a3", label: "beach", score: 0.9, reason: "sharper" }] },
    ] });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    fireEvent.click(screen.getByRole("button", { name: /Make my video/ }));
    await waitFor(() => expect(screen.getByText(/Your video is ready/)).toBeTruthy(), { timeout: 4000 });
    // The alternative clip is offered and swapping calls the replace endpoint.
    fireEvent.click(screen.getByRole("button", { name: /^beach$/ }));
    await waitFor(() => expect(api.replaceSlot).toHaveBeenCalledWith("p1", 0, "a3"));
  });

  it("blocks Save until required review items are acknowledged (increment #3)", async () => {
    twoCandidates();
    (api.review as ReturnType<typeof vi.fn>).mockResolvedValue({
      required_ack_ids: ["claim-0"],
      groups: [{ key: "claims", title: "Words on screen", note: "Confirm each line.",
        items: [{ id: "claim-0", label: "50% off today", detail: "Confirm it's accurate.",
          kind: "claim", requires_ack: true }] }],
    });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    fireEvent.click(screen.getByRole("button", { name: /Make my video/ }));
    await waitFor(() => expect(screen.getByText(/Your video is ready/)).toBeTruthy(), { timeout: 4000 });
    expect((screen.getByRole("button", { name: /Save video/ }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("checkbox"));
    expect((screen.getByRole("button", { name: /Save video/ }) as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: /Save video/ }));
    await waitFor(() => expect(api.approve).toHaveBeenCalledWith("p1", "enhanced", undefined, ["claim-0"]));
  });

  it("offers one-tap auto-save only once trust is earned (increment #4)", async () => {
    (api.trust as ReturnType<typeof vi.fn>).mockResolvedValue({ approvals: 5, threshold: 5, remaining: 0,
      autopilot_unlocked: true, default_output_dir: "/Users/me/Movies/out", ready_for_one_tap: true });
    render(<CreateFlow onDone={() => {}} />);
    typeFolder();
    await waitFor(() => expect(screen.getByRole("button", { name: /Make & save automatically/ })).toBeTruthy());
    expect(screen.getByRole("button", { name: /Review before saving/ })).toBeTruthy();
  });
});
