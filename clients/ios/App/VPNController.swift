import Foundation
import NetworkExtension
import Combine

@MainActor protocol VPNEntry: AnyObject {
    var provider: String? { get }
    var configuration: [String: Any]? { get }
    var status: NEVPNStatus { get }
    func configure(_ handoff: Handoff, provider: String)
    func save() async throws
    func reload() async throws
    func start() throws
    func stop()
    func observe(_ update: @escaping () -> Void)
    func lastError() async -> Error?
}

@MainActor protocol VPNPreferences {
    func load() async throws -> [VPNEntry]
    func make() -> VPNEntry
}

@MainActor final class SystemVPNEntry: VPNEntry {
    private let manager: NETunnelProviderManager
    private var observation: NSObjectProtocol?
    init(_ manager: NETunnelProviderManager) { self.manager = manager }
    deinit { if let observation = observation { NotificationCenter.default.removeObserver(observation) } }
    var provider: String? { (manager.protocolConfiguration as? NETunnelProviderProtocol)?.providerBundleIdentifier }
    var configuration: [String: Any]? { (manager.protocolConfiguration as? NETunnelProviderProtocol)?.providerConfiguration }
    var status: NEVPNStatus { manager.connection.status }
    func configure(_ handoff: Handoff, provider: String) {
        let settings = NETunnelProviderProtocol()
        settings.providerBundleIdentifier = provider
        settings.providerConfiguration = handoff.configuration
        settings.serverAddress = "Family Connect development MESH"
        settings.includeAllNetworks = false; settings.enforceRoutes = false
        manager.protocolConfiguration = settings
        manager.localizedDescription = "Family Connect development"
        manager.isEnabled = true; manager.isOnDemandEnabled = false; manager.onDemandRules = []
    }
    func save() async throws {
        try await withCheckedThrowingContinuation { (reply: CheckedContinuation<Void, Error>) in
            manager.saveToPreferences { error in if let error = error { reply.resume(throwing: error) } else { reply.resume() } }
        }
    }
    func reload() async throws {
        try await withCheckedThrowingContinuation { (reply: CheckedContinuation<Void, Error>) in
            manager.loadFromPreferences { error in if let error = error { reply.resume(throwing: error) } else { reply.resume() } }
        }
    }
    func start() throws {
        guard let session = manager.connection as? NETunnelProviderSession else { throw SafeFailure(message: "Provider session missing") }
        try session.startTunnel(options: nil)
    }
    func stop() { manager.connection.stopVPNTunnel() }
    func lastError() async -> Error? {
        await withCheckedContinuation { reply in
            manager.connection.fetchLastDisconnectError { reply.resume(returning: $0) }
        }
    }
    func observe(_ update: @escaping () -> Void) {
        if let observation = observation { NotificationCenter.default.removeObserver(observation) }
        observation = NotificationCenter.default.addObserver(forName: .NEVPNStatusDidChange, object: manager.connection, queue: .main) { _ in
            Task { @MainActor in update() }
        }
    }
}

@MainActor struct SystemVPNPreferences: VPNPreferences {
    func load() async throws -> [VPNEntry] {
        let managers: [NETunnelProviderManager] = try await withCheckedThrowingContinuation { reply in
            NETunnelProviderManager.loadAllFromPreferences { managers, error in
                if let error = error { reply.resume(throwing: error) }
                else { reply.resume(returning: managers ?? []) }
            }
        }
        return managers.map { SystemVPNEntry($0) }
    }
    func make() -> VPNEntry { SystemVPNEntry(NETunnelProviderManager()) }
}

@MainActor final class VPNController: ObservableObject {
    @Published var selectedReference = ""
    @Published var selectedID = "1E30B0FA-1A16-4580-AC82-6638503C76AF"
    @Published private(set) var references: [String] = []
    @Published private(set) var identifiers: [String] = []
    @Published private(set) var status: NEVPNStatus = .invalid
    @Published private(set) var busy = false
    @Published private(set) var message = "Development only; physical VPN acceptance NOT_RUN"
    private let preferences: VPNPreferences
    private let store: () throws -> MaterialStore
    private let provider: String
    private var current: VPNEntry?
    private var generation = 0
    private var requested = false

    init(preferences: VPNPreferences? = nil, provider: String? = nil,
         store: @escaping () throws -> MaterialStore = MaterialStore.configured) {
        self.preferences = preferences ?? SystemVPNPreferences(); self.store = store
        self.provider = provider ?? (Bundle.main.object(forInfoDictionaryKey: "FCTunnelBundleID") as? String ?? "")
    }
    var statusText: String {
        switch status {
        case .invalid: return "Not configured / invalid"
        case .disconnected: return "Disconnected"
        case .connecting: return "Connecting (system)"
        case .connected: return "Connected (system status; not traffic proof)"
        case .reasserting: return "Reasserting"
        case .disconnecting: return "Disconnecting (system)"
        @unknown default: return "Unknown system status"
        }
    }
    private func inactive(_ entry: VPNEntry) -> Bool { entry.status == .disconnected || entry.status == .invalid }
    private func check(_ token: Int) throws {
        guard token == generation else { throw SafeFailure(message: "Operation cancelled") }
    }
    private func attach(_ entry: VPNEntry) {
        current = entry; status = entry.status
        entry.observe { [weak self, weak entry] in
            guard let self = self, let entry = entry, self.current === entry else { return }
            self.status = entry.status
            if entry.status == .disconnected || entry.status == .invalid {
                self.requested = false
                let token = self.generation
                Task { @MainActor [weak self, weak entry] in
                    guard let self = self, let entry = entry else { return }
                    let error = await entry.lastError()
                    guard self.current === entry, self.generation == token, self.inactive(entry) else { return }
                    if let error = error { self.message = safeMessage(error) }
                }
            }
        }
    }
    private func owned() async throws -> [VPNEntry] {
        guard !provider.isEmpty else { throw SafeFailure(message: "Provider build identifier missing") }
        let entries = try await preferences.load().filter { $0.provider == provider }
        let ids = try entries.map { try Handoff(configuration: $0.configuration).identifier }
        guard Set(ids).count == ids.count else { throw SafeFailure(message: "Duplicate VPN identifier; inspect configurations manually") }
        identifiers = ids.sorted()
        return entries
    }
    func refresh() async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        let token = generation
        do {
            let entries = try await owned(); try check(token)
            if let entry = entries.first(where: { (try? Handoff(configuration: $0.configuration).identifier) == selectedID }) {
                attach(entry)
                selectedReference = try Handoff(configuration: entry.configuration).reference
            } else { current = nil; status = .invalid }
            references = try store().references()
        } catch { message = safeMessage(error) }
    }
    func prepare(connect: Bool) async {
        guard !busy && !requested else { message = "Operation already in progress"; return }
        generation += 1
        busy = true; defer { busy = false }
        let token = generation
        do {
            let entries = try await owned(); try check(token)
            let existing = entries.first { (try? Handoff(configuration: $0.configuration).identifier) == selectedID }
            guard !entries.contains(where: { !inactive($0) }) else { throw SafeFailure(message: "Disconnect the active development VPN before changing or connecting") }
            let handoff = try Handoff(reference: selectedReference, identifier: selectedID)
            _ = try store().load(handoff.reference)
            let entry = existing ?? preferences.make()
            attach(entry)
            entry.configure(handoff, provider: provider)
            try await entry.save(); try check(token)
            try await entry.reload(); try check(token)
            let saved = try Handoff(configuration: entry.configuration)
            guard entry.provider == provider, saved.identifier == handoff.identifier, saved.reference == handoff.reference else {
                throw SafeFailure(message: "Saved VPN configuration does not match selected material")
            }
            attach(entry)
            if connect {
                _ = try store().load(handoff.reference)
                try check(token)
                requested = true
                do { try entry.start() } catch { requested = false; throw error }
                status = entry.status
                message = "Start requested; wait for system status. No traffic acceptance is implied."
            } else { message = "Configuration saved and reloaded; not connected" }
        } catch { message = safeMessage(error) }
    }
    func disconnect() {
        generation += 1; requested = false
        current?.stop(); status = current?.status ?? .invalid
        message = "Stop requested; ordinary OS routing may resume"
    }
    func importData(_ data: Data) throws {
        guard !busy else { throw SafeFailure(message: "Wait for the current operation") }
        let vault = try store()
        selectedReference = try vault.insert(data)
        references = try vault.references()
        message = "New immutable material imported; existing session/configuration unchanged"
    }
    func importFile(_ url: URL) {
        do {
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            let file = try FileHandle(forReadingFrom: url); defer { try? file.close() }
            let data = try file.read(upToCount: 96 * 1024 + 1) ?? Data()
            try importData(data)
        } catch { message = safeMessage(error) }
    }
    func importFailed(_ error: Error) { message = safeMessage(error) }
    func removeMaterial(revoke: Bool) async {
        guard !busy && !requested else { message = "Disconnect and wait before material removal"; return }
        busy = true; defer { busy = false }
        let token = generation
        do {
            let entries = try await owned(); try check(token)
            guard entries.allSatisfy(inactive) else { throw SafeFailure(message: "Disconnect all development sessions before removal") }
            let vault = try store()
            if revoke { try vault.revoke(selectedReference) } else { try vault.delete(selectedReference) }
            references = try vault.references()
            message = "Material removed/revoked; referencing configurations cannot start. No VPN configurations were deleted."
        } catch { message = safeMessage(error) }
    }
}
