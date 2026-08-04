import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./api", () => {
  class CoachError extends Error { code: string; constructor(c: string, m: string) { super(m); this.code = c; } }
  return {
    CoachError,
    api: {
      listProjects: vi.fn().mockResolvedValue({ projects: [] }),
      storage: vi.fn().mockResolvedValue({ free_gb: 77, total_gb: 500 }),
      doctor: vi.fn().mockResolvedValue({ checks: {}, macos_only_checks_blocked: false }),
      cacheSize: vi.fn().mockResolvedValue({ bytes: 0 }),
      createProject: vi.fn().mockResolvedValue({ id: "p1", title: "New video", step: "sources", status: "new", style_dna_version: null }),
      preflight: vi.fn(),
    },
  };
});

import App from "./App";
import { api } from "./api";

beforeEach(() => vi.clearAllMocks());

describe("App shell", () => {
  it("shows the five destinations and a private-on-this-Mac note", async () => {
    render(<App />);
    for (const label of ["Home", "Projects", "My Style", "Connections", "Settings"]) {
      expect(screen.getByRole("button", { name: new RegExp(label) })).toBeTruthy();
    }
    expect(screen.getAllByText(/Private on this Mac/).length).toBeGreaterThan(0);
  });

  it("leads Home with the outcome and a single primary action", async () => {
    render(<App />);
    expect(screen.getByText(/Turn raw footage into a finished video/)).toBeTruthy();
    expect(screen.getAllByRole("button", { name: /Make a video/ }).length).toBeGreaterThan(0);
  });

  it("first-run Home shows an empty state, not fake actions", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText(/No videos yet/)).toBeTruthy());
  });

  it("navigates to Create when Make a video is pressed", async () => {
    render(<App />);
    fireEvent.click(screen.getAllByRole("button", { name: /Make a video/ })[0]);
    await waitFor(() => expect(screen.getByText(/Add your clips/)).toBeTruthy());
    // Make my video is disabled until a footage folder is chosen.
    const make = screen.getByRole("button", { name: /Make my video/ }) as HTMLButtonElement;
    expect(make.disabled).toBe(true);
    expect(api.createProject).not.toHaveBeenCalled(); // no throwaway project yet
  });
});
