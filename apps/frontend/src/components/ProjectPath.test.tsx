import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProjectPath } from "./ProjectPath";

describe("ProjectPath (truthful workflow)", () => {
  it("marks the current step", () => {
    render(<ProjectPath current="render" />);
    const current = screen.getByText(/Render/).closest("li");
    expect(current?.getAttribute("aria-current")).toBe("step");
  });

  it("renders the four truthful steps and no CapCut finishing step", () => {
    render(<ProjectPath current="sources" />);
    for (const label of ["Sources", "Coach Edit", "Render", "Review & Learn"]) {
      expect(screen.getByText(new RegExp(label))).toBeTruthy();
    }
    expect(screen.queryByText(/Finish in CapCut/)).toBeNull();
  });
});
