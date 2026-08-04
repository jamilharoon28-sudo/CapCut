// swift-tools-version:5.9
// CapCut Coach mac-bridge — a small, read-only native probe.
// Builds and runs ONLY on macOS. It reports app/process/version, performs a
// read-only Accessibility probe (never clicks), and can post notifications.
import PackageDescription

let package = Package(
    name: "mac-bridge",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "mac-bridge", path: "Sources/mac-bridge")
    ]
)
