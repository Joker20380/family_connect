import SwiftUI
import UniformTypeIdentifiers

@main
@MainActor
struct FamilyConnectApp: App {
    @StateObject private var vpn = VPNController()
    @State private var importing = false
    @State private var report = "Unsigned iOS MESH laboratory. No VPN or Telemost acceptance."
    @State private var running = false

    var body: some Scene {
        WindowGroup {
            ScrollView { VStack(alignment: .leading, spacing: 16) {
                Text("Family Connect · MESH").font(.title)
                Text("Development candidate · not an always-on VPN or kill switch").font(.headline)
                Text(vpn.statusText).accessibilityIdentifier("vpn-status")
                Text(vpn.message).font(.footnote)
                Picker("Configuration", selection: $vpn.selectedID) {
                    ForEach(Array(Set(vpn.identifiers + [vpn.selectedID])).sorted(), id: \.self) { Text($0).tag($0) }
                }.disabled(vpn.busy)
                Picker("Test material reference", selection: $vpn.selectedReference) {
                    Text("Select imported material").tag("")
                    ForEach(vpn.references, id: \.self) { Text($0).tag($0) }
                }.disabled(vpn.busy)
                Button("Import test material…") { importing = true }.disabled(vpn.busy)
                Button("Reload saved VPN configurations") { Task { await vpn.refresh() } }.disabled(vpn.busy)
                Button("Save / update selected VPN") { Task { await vpn.prepare(connect: false) } }.disabled(vpn.busy)
                Button("Connect") { Task { await vpn.prepare(connect: true) } }.disabled(vpn.busy)
                Button("Disconnect / cancel startup") { vpn.disconnect() }
                Button("Revoke selected material", role: .destructive) { Task { await vpn.removeMaterial(revoke: true) } }.disabled(vpn.busy)
                Button("Delete selected material", role: .destructive) { Task { await vpn.removeMaterial(revoke: false) } }.disabled(vpn.busy)
                DisclosureGroup("Isolated diagnostics (not a VPN)") {
                    Text(report).accessibilityIdentifier("mesh-report")
                    Button("Run isolated packet / lifecycle checks") { runChecks() }.disabled(running)
                }
                Text("System Connected is not proof of MESH traffic, correct routing or absence of leaks. Disconnect restores ordinary OS routing. Real identity and device acceptance are separate.").font(.footnote)
            }.padding() }.fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
                if case .success(let url) = result { vpn.importFile(url) }
            }.task {
                if !ProcessInfo.processInfo.arguments.contains("--self-test") { await vpn.refresh() }
            }.onAppear {
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
