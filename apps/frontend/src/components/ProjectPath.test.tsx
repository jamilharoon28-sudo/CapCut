import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProjectPath } from "./ProjectPath";

describe("ProjectPath", () => {
  it("marks the current step", () => {
    render(<ProjectPath current="edit" />);
    const current = screen.getByText("Coach Edit").closest("li");
    expect(current?.getAttribute("aria-current")).toBe("step");
  });

  it("renders all five steps", () => {
    render(<ProjectPath current="sources" />);
    for (const label of [
      "Sources",
      "Script & Story",
      "Coach Edit",
      "Finish in CapCut",
      "Review & Learn",
    ]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });
});
