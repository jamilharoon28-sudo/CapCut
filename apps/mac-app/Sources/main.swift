// CapCut Coach.app — native launcher shell (macOS).
//
// A thin AppKit + WKWebView window that:
//   1. starts the local FastAPI backend as a child process on a free loopback port,
//      pointing it at the bundled React build (single process, one origin);
//   2. waits for /api/v1/health;
//   3. reads the per-install bearer token from Application Support and injects it
//      as window.__COACH_TOKEN__ (never sent over the wire);
//   4. loads the UI and cleanly stops the backend on quit.
//
// Build config is read from Resources/launch.json (written by build-macos-app.sh):
//   { "python": "/abs/path/.venv/bin/python", "backendDir": "/abs/.../apps/backend",
//     "frontendDist": "<in-bundle>" }
//
// This file is authored for macOS; it is not compiled in the Linux CI scaffold.

import AppKit
import WebKit

func log(_ s: String) { FileHandle.standardError.write((s + "\n").data(using: .utf8)!) }

// A free loopback TCP port.
func freePort() -> Int {
    let fd = socket(AF_INET, SOCK_STREAM, 0)
    var addr = sockaddr_in()
    addr.sin_family = sa_family_t(AF_INET)
    addr.sin_addr.s_addr = inet_addr("127.0.0.1")
    addr.sin_port = 0
    _ = withUnsafePointer(to: &addr) {
        $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size)) }
    }
    var len = socklen_t(MemoryLayout<sockaddr_in>.size)
    withUnsafeMutablePointer(to: &addr) {
        $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { _ = getsockname(fd, $0, &len) }
    }
    let port = Int(UInt16(bigEndian: addr.sin_port))
    close(fd)
    return port
}

func supportDir() -> URL {
    FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("CapCut Coach", isDirectory: true)
}

struct LaunchConfig: Decodable {
    let python: String
    let backendDir: String
    let frontendDist: String
    let ffmpeg: String?
    let ffprobe: String?
}

func loadConfig() -> LaunchConfig? {
    guard let res = Bundle.main.resourcePath else { return nil }
    let url = URL(fileURLWithPath: res).appendingPathComponent("launch.json")
    guard let data = try? Data(contentsOf: url) else { return nil }
    return try? JSONDecoder().decode(LaunchConfig.self, from: data)
}

final class Backend {
    let process = Process()
    let port: Int
    init(config: LaunchConfig, port: Int) {
        self.port = port
        process.executableURL = URL(fileURLWithPath: config.python)
        process.arguments = ["-m", "capcut_coach"]
        process.currentDirectoryURL = URL(fileURLWithPath: config.backendDir)
        var env = ProcessInfo.processInfo.environment
        env["COACH_PORT"] = String(port)
        env["COACH_FRONTEND_DIST"] = config.frontendDist
        // A GUI app does not inherit the shell PATH; make Homebrew tools findable
        // and pass explicit ffmpeg/ffprobe paths recorded at build time.
        let extraPaths = "/opt/homebrew/bin:/usr/local/bin"
        env["PATH"] = extraPaths + ":" + (env["PATH"] ?? "/usr/bin:/bin")
        if let ff = config.ffmpeg, !ff.isEmpty { env["COACH_FFMPEG"] = ff }
        if let fp = config.ffprobe, !fp.isEmpty { env["COACH_FFPROBE"] = fp }
        process.environment = env
    }
    func start() throws { try process.run() }
    func stop() { if process.isRunning { process.terminate() } }
}

func waitForHealth(port: Int, timeout: TimeInterval = 20) -> Bool {
    let url = URL(string: "http://127.0.0.1:\(port)/api/v1/health")!
    let deadline = Date().addingTimeInterval(timeout)
    while Date() < deadline {
        let sem = DispatchSemaphore(value: 0)
        var ok = false
        let task = URLSession.shared.dataTask(with: url) { _, resp, _ in
            ok = (resp as? HTTPURLResponse)?.statusCode == 200; sem.signal()
        }
        task.resume()
        _ = sem.wait(timeout: .now() + 1.5)
        if ok { return true }
        Thread.sleep(forTimeInterval: 0.4)
    }
    return false
}

func readToken() -> String {
    let url = supportDir().appendingPathComponent("auth-token")
    return (try? String(contentsOf: url, encoding: .utf8))?
        .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var backend: Backend?

    func applicationDidFinishLaunching(_ note: Notification) {
        guard let config = loadConfig() else { fatalError("missing launch.json") }
        let port = freePort()
        let backend = Backend(config: config, port: port)
        self.backend = backend
        do { try backend.start() } catch { log("backend failed: \(error)") }

        // Inject the bearer token before any page script runs.
        let controller = WKUserContentController()
        DispatchQueue.global().async {
            let healthy = waitForHealth(port: port)
            let token = readToken()
            DispatchQueue.main.async {
                let js = "window.__COACH_TOKEN__ = \"\(token)\";"
                controller.addUserScript(WKUserScript(source: js,
                    injectionTime: .atDocumentStart, forMainFrameOnly: true))
                let cfg = WKWebViewConfiguration()
                cfg.userContentController = controller
                self.webView = WKWebView(frame: .zero, configuration: cfg)
                self.window.contentView = self.webView
                let target = healthy ? "http://127.0.0.1:\(port)/"
                                     : "data:text/html,<h2>Could not start CapCut Coach.</h2>"
                self.webView.load(URLRequest(url: URL(string: target)!))
            }
        }

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1200, height: 800),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered, defer: false)
        window.title = "CapCut Coach"
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ note: Notification) { backend?.stop() }
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
