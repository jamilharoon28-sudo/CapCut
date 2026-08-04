import { useState } from "react";

import { nativePickerAvailable, pickNative, type PickKind } from "../native";
import { Button, SourceCard, type IconName } from "./ui";

// A source picker: uses the native Mac panel when available, and always keeps a
// clearly-labelled paste-path fallback for browser/recovery mode.
export function PathField({
  icon, title, kind, required, value, onChange, hint,
}: {
  icon: IconName; title: string; kind: PickKind; required?: boolean;
  value: string; onChange: (v: string) => void; hint?: string;
}) {
  const native = nativePickerAvailable();
  const [showPaste, setShowPaste] = useState(!native);

  async function choose() {
    try {
      const picked = await pickNative(kind);
      if (picked) onChange(picked);
    } catch {
      setShowPaste(true);
    }
  }

  return (
    <div>
      <SourceCard
        icon={icon}
        title={title}
        required={required}
        value={value || null}
        hint={hint}
        action={
          native
            ? <Button size="md" onClick={choose}>Choose…</Button>
            : <Button size="md" onClick={() => setShowPaste((s) => !s)}>Add</Button>
        }
      />
      {(showPaste || (!native && !value)) && (
        <div className="field" style={{ marginTop: 8 }}>
          <input
            className="input"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={kind === "folder" ? "/Users/you/Movies/raw-footage" : "/Users/you/file"}
            aria-label={`${title} path`}
          />
          <span className="small muted">
            {native ? "Or paste a path" : "In Finder: right-click → Copy as Pathname, then paste."}
          </span>
        </div>
      )}
    </div>
  );
}
