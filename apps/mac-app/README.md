# CapCut Coach.app shell (macOS only)

The normal user launches a native `CapCut Coach.app` — a thin Swift + `WKWebView`
shell around the local React UI and FastAPI service (design system §2). The shell
owns:

- native folder/file pickers and security-scoped bookmarks;
- Keychain storage for the loopback bearer token;
- process detection and CapCut version reads (delegated to `apps/mac-bridge`);
- Accessibility permission prompts and user-triggered screenshots;
- user notifications.

A browser at `http://127.0.0.1:<port>` is the **recovery fallback**.

## Status

⛔ **BLOCKED BY EVIDENCE** in this Linux CI scaffold — an Xcode/Swift app target
cannot be built or run here. The shell is a small wrapper; the substantive logic
lives in `apps/backend`, `apps/frontend`, and the read-only `apps/mac-bridge`
(whose Swift source is authored). Build the shell on the target Mac as the final
packaging step (Phase 10).

## Shape (to implement on macOS)

```
CapCutCoachApp (SwiftUI)
 └─ WKWebView → loads http://127.0.0.1:<port> after starting the launchd service
 └─ injects window.__COACH_TOKEN__ from Keychain
 └─ bridges native pickers / notifications to the web layer via WKScriptMessageHandler
```
