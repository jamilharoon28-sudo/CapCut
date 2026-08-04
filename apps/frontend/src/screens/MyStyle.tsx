import { Icon, SectionHeader } from "../components/ui";

// Honest: Coach starts with sensible editing rules and learns preferences over
// time. Learning-from-examples ingestion is not implemented yet, so we present
// an explanatory state — not a fake upload button.
export function MyStyle() {
  return (
    <div className="container">
      <SectionHeader title="My Style" subtitle="Starts smart. Learns what you like." />
      <div className="card stack">
        <p className="muted" style={{ margin: 0 }}>
          Coach begins with good defaults for short vertical video — a strong opening, clean cuts,
          readable captions, subject-aware framing, and a call to action before the end. As you
          approve videos and pick favourites, it nudges pacing, caption density, framing and flair
          toward your taste.
        </p>
        <div className="divider" />
        <div className="row" style={{ gap: 16 }}>
          {[
            ["wand", "Tasteful flair", "Bounded so clips stay intelligible"],
            ["scissors", "Disciplined pacing", "No over-cutting or effect spam"],
            ["text", "Caption style", "Learns density and emphasis you prefer"],
          ].map(([icon, t, s]) => (
            <div className="cap" key={t} style={{ flex: "1 1 200px" }}>
              <div className="ico"><Icon name={icon as "wand"} /></div>
              <div><strong>{t}</strong><div className="small muted">{s}</div></div>
            </div>
          ))}
        </div>
        <div className="divider" />
        <p className="small muted" style={{ margin: 0 }}>
          Learning from matched raw/finished example videos will improve this further. That import
          flow isn’t available yet — when it is, your originals stay read-only.
        </p>
      </div>
    </div>
  );
}
