// CapCut Coach mac-bridge (Phase 0, P0.4 + Phase 1 process/version).
//
// READ-ONLY by contract. This tool NEVER clicks, types, or changes anything in
// CapCut. It exposes three subcommands the Python service shells out to:
//
//   mac-bridge version               -> CapCut bundle version/build/source (JSON)
//   mac-bridge is-running            -> {"running": bool}
//   mac-bridge probe                 -> read-only Accessibility tree summary (JSON)
//
// The Accessibility probe requires the user to grant permission in
// System Settings → Privacy & Security → Accessibility. Without it, `probe`
// returns {"granted": false} rather than guessing.

import AppKit
import ApplicationServices
import Foundation

func emit(_ obj: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
}

func capcutBundleURL() -> URL? {
    let candidates = [
        "/Applications/CapCut.app",
        NSString(string: "~/Applications/CapCut.app").expandingTildeInPath,
    ]
    for path in candidates where FileManager.default.fileExists(atPath: path) {
        return URL(fileURLWithPath: path)
    }
    return nil
}

func versionInfo() -> [String: Any] {
    guard let url = capcutBundleURL(),
          let bundle = Bundle(url: url),
          let info = bundle.infoDictionary else {
        return ["found": false, "reason": "CapCut.app not found"]
    }
    return [
        "found": true,
        "path": url.path,
        "short_version": info["CFBundleShortVersionString"] as? String ?? "",
        "build": info["CFBundleVersion"] as? String ?? "",
        "app_source": (info["appSource"] as? String
            ?? info["CPAppSource"] as? String ?? "").lowercased(),
    ]
}

func isRunning() -> Bool {
    NSWorkspace.shared.runningApplications.contains { app in
        (app.bundleIdentifier ?? "").lowercased().contains("capcut")
            || (app.localizedName ?? "").lowercased() == "capcut"
    }
}

// Read-only walk of the frontmost CapCut window's accessibility elements.
func probe() -> [String: Any] {
    guard AXIsProcessTrusted() else {
        return ["granted": false,
                "hint": "Grant Accessibility permission to enable read-only inspection."]
    }
    guard let app = NSWorkspace.shared.runningApplications.first(where: {
        ($0.bundleIdentifier ?? "").lowercased().contains("capcut")
    }) else {
        return ["granted": true, "capcut_running": false]
    }
    let axApp = AXUIElementCreateApplication(app.processIdentifier)
    var windowsRef: CFTypeRef?
    AXUIElementCopyAttributeValue(axApp, kAXWindowsAttribute as CFString, &windowsRef)
    var controls: [[String: String]] = []
    if let windows = windowsRef as? [AXUIElement], let front = windows.first {
        summarise(front, into: &controls, depth: 0, maxDepth: 3, cap: 200)
    }
    return ["granted": true, "capcut_running": true, "controls": controls]
}

func summarise(_ el: AXUIElement, into out: inout [[String: String]],
               depth: Int, maxDepth: Int, cap: Int) {
    if out.count >= cap || depth > maxDepth { return }
    var role: CFTypeRef?
    var title: CFTypeRef?
    var ident: CFTypeRef?
    AXUIElementCopyAttributeValue(el, kAXRoleAttribute as CFString, &role)
    AXUIElementCopyAttributeValue(el, kAXTitleAttribute as CFString, &title)
    AXUIElementCopyAttributeValue(el, kAXIdentifierAttribute as CFString, &ident)
    out.append([
        "role": (role as? String) ?? "",
        "title": (title as? String) ?? "",
        "identifier": (ident as? String) ?? "",
    ])
    var childrenRef: CFTypeRef?
    AXUIElementCopyAttributeValue(el, kAXChildrenAttribute as CFString, &childrenRef)
    if let children = childrenRef as? [AXUIElement] {
        for child in children { summarise(child, into: &out, depth: depth + 1,
                                          maxDepth: maxDepth, cap: cap) }
    }
}

// --- entry point ---
let arg = CommandLine.arguments.dropFirst().first ?? "version"
switch arg {
case "version":    emit(versionInfo())
case "is-running": emit(["running": isRunning()])
case "probe":      emit(probe())
default:           emit(["error": "unknown command \(arg)"])
}
