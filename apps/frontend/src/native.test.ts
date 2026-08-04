import { afterEach, describe, expect, it, vi } from "vitest";

import { nativePickerAvailable, pickNative } from "./native";

afterEach(() => {
  delete (window as unknown as { webkit?: unknown }).webkit;
  delete (window as unknown as { __coachPickerResolvers?: unknown }).__coachPickerResolvers;
  delete (window as unknown as { __coachPickerResolve?: unknown }).__coachPickerResolve;
});

describe("native picker bridge", () => {
  it("reports unavailable in a plain browser", () => {
    expect(nativePickerAvailable()).toBe(false);
  });

  it("rejects when no native handler is present", async () => {
    await expect(pickNative("folder")).rejects.toThrow(/unavailable/);
  });

  it("posts a message and resolves via the shell callback", async () => {
    const postMessage = vi.fn();
    (window as unknown as { webkit: unknown }).webkit = {
      messageHandlers: { coachPicker: { postMessage } },
    };
    const promise = pickNative("folder");
    expect(postMessage).toHaveBeenCalledTimes(1);
    const sent = postMessage.mock.calls[0][0] as { requestId: string; kind: string };
    expect(sent.kind).toBe("folder");
    // Simulate the Swift shell returning a chosen path.
    window.__coachPickerResolve!(sent.requestId, "/Users/me/Movies/raw");
    await expect(promise).resolves.toBe("/Users/me/Movies/raw");
  });

  it("resolves null when the user cancels", async () => {
    const postMessage = vi.fn();
    (window as unknown as { webkit: unknown }).webkit = {
      messageHandlers: { coachPicker: { postMessage } },
    };
    const promise = pickNative("image");
    const sent = postMessage.mock.calls[0][0] as { requestId: string };
    window.__coachPickerResolve!(sent.requestId, null);
    await expect(promise).resolves.toBeNull();
  });
});
