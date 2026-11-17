import SwiftUI

@main
struct FamilyConnectApp: App {
    @State private var report = "Unsigned iOS MESH laboratory. No VPN or Telemost acceptance."
    @State private var running = false

    var body: some Scene {
        WindowGroup {
            VStack(alignment: .leading, spacing: 20) {
                Text("Family Connect · MESH").font(.title)
                Text("Swift → C → Go → existing Xray/gVisor → wholedevice").font(.headline)
                Text(report).accessibilityIdentifier("mesh-report")
                Button("Run isolated packet checks") { runChecks() }.disabled(running)
                Text("A synthetic DNS data plane is used only in this laboratory. The extension uses signed Family bootstrap, TLS, ReliableStream and Telemost VP8/RTP; real network tests require a provisioned iPhone.").font(.footnote)
            }.padding().onAppear {
                if ProcessInfo.processInfo.arguments.contains("--self-test") { runChecks() }
            }
        }
    }

    private func runChecks() {
        guard !running else { return }
        running = true
        DispatchQueue.global().async {
            let result = SelfTests.run()
            if ProcessInfo.processInfo.arguments.contains("--self-test") {
                let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("self-test.json")
                do {
                    try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]).write(to: url, options: .atomic)
                } catch { print("FC_IOS_RECEIPT_WRITE_FAILED") }
                print("FC_IOS_ISOLATED_RESULT \(result["passed"] ?? false)")
            }
            DispatchQueue.main.async {
                report = String(describing: result)
                running = false
            }
        }
    }
}
