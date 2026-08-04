// Native Mac picker bridge. On macOS the app shell exposes a `coachPicker`
// WKScriptMessageHandler that opens NSOpenPanel and returns the chosen path.
// In the browser (dev/recovery) this is unavailable and callers fall back to a
// paste-path field. Nothing here scans the filesystem — it only asks the shell.

export type PickKind = "folder" | "audio" | "image" | "script";

declare global {
  interface Window {
    webkit?: { messageHandlers?: { coachPicker?: { postMessage: (m: unknown) => void } } };
    __coachPickerResolvers?: Record<string, (path: string | null) => void>;
    __coachPickerResolve?: (id: string, path: string | null) => void;
  }
}

let counter = 0;

export function nativePickerAvailable(): boolean {
  return typeof window !== "undefined" && !!window.webkit?.messageHandlers?.coachPicker;
}

/** Ensure the single global resolver the Swift shell calls back into exists. */
export function installPickerResolver(): void {
  if (typeof window === "undefined") return;
  window.__coachPickerResolvers ??= {};
  if (!window.__coachPickerResolve) {
    window.__coachPickerResolve = (id: string, path: string | null) => {
      const resolver = window.__coachPickerResolvers?.[id];
      if (resolver) {
        resolver(path && path.length ? path : null);
        delete window.__coachPickerResolvers![id];
      }
    };
  }
}

/** Open a native picker and resolve to the chosen path, or null if cancelled. */
export function pickNative(kind: PickKind): Promise<string | null> {
  installPickerResolver();
  const handler = window.webkit?.messageHandlers?.coachPicker;
  if (!handler) return Promise.reject(new Error("native picker unavailable"));
  const requestId = `pick_${Date.now()}_${counter++}`;
  return new Promise<string | null>((resolve) => {
    window.__coachPickerResolvers![requestId] = resolve;
    handler.postMessage({ requestId, kind });
  });
}
