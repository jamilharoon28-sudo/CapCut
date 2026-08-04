import { Component, type ReactNode } from "react";

import { Button, EmptyState } from "./ui";

type Props = { children: ReactNode };
type State = { error: Error | null };

// Catches render errors so the whole app never shows a blank screen or a stack
// trace to the user. Originals are never affected by a UI error.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error) {
    // Keep diagnostic detail in the console/local logs, not on screen.
    console.error("[CapCut Coach] UI error:", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="main">
          <div className="container">
            <EmptyState
              icon="alert"
              title="Something on this screen stopped working"
              body="Your videos and original footage are safe. Reload to continue."
              action={<Button variant="primary" onClick={() => location.reload()}>Reload</Button>}
            />
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
