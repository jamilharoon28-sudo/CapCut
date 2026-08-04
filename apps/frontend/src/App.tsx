import { useState } from "react";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { Icon, type IconName } from "./components/ui";
import { Connections } from "./screens/Connections";
import { CreateFlow } from "./screens/CreateFlow";
import { Home } from "./screens/Home";
import { MyStyle } from "./screens/MyStyle";
import { Projects } from "./screens/Projects";
import { Settings } from "./screens/Settings";

type Dest = "Home" | "Projects" | "My Style" | "Connections" | "Settings" | "Create";
const NAV: { key: Dest; icon: IconName }[] = [
  { key: "Home", icon: "home" },
  { key: "Projects", icon: "folder" },
  { key: "My Style", icon: "sparkles" },
  { key: "Connections", icon: "link" },
  { key: "Settings", icon: "gear" },
];

export default function App() {
  const [dest, setDest] = useState<Dest>("Home");

  return (
    <div className="app">
      <nav className="sidebar" aria-label="Primary">
        <div className="brand"><span className="dot" /><span>CapCut Coach</span></div>
        {NAV.map((n) => (
          <button key={n.key} className="nav-btn" aria-current={dest === n.key ? "page" : undefined}
            onClick={() => setDest(n.key)}>
            <Icon name={n.icon} /><span>{n.key}</span>
          </button>
        ))}
        <div className="nav-spacer" />
        <div className="privacy-note"><Icon name="lock" size={16} /><span>Private on this Mac</span></div>
      </nav>

      <main className="main">
        <ErrorBoundary>
          {dest === "Home" && <Home onCreate={() => setDest("Create")} onOpenProjects={() => setDest("Projects")} />}
          {dest === "Create" && <CreateFlow onDone={() => setDest("Projects")} />}
          {dest === "Projects" && <Projects onCreate={() => setDest("Create")} />}
          {dest === "My Style" && <MyStyle />}
          {dest === "Connections" && <Connections />}
          {dest === "Settings" && <Settings />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
