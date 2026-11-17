import Foundation
import NetworkExtension
import Security

private final class FixturePath: PathWatcher {
    var callback: ((String?) -> Void)?
    var stopped = false
    func start(_ update: @escaping (String?) -> Void) { callback = update; update("synthetic0") }
    func stop() { stopped = true }
}

private final class FixtureKeychain: KeychainDriver {
    var entries: [String: Data] = [:]
    var failure: OSStatus?
    var last: [String: Any] = [:]
    func perform(_ operation: KeychainOperation, query: [String: Any]) -> (OSStatus, Any?) {
        last = query
        if let failure = failure { return (failure, nil) }
        let account = query[kSecAttrAccount as String] as? String
        switch operation {
        case .add, .update:
            guard let account = account, let data = query[kSecValueData as String] as? Data else { return (errSecParam, nil) }
            if operation == .update && entries[account] == nil { return (errSecItemNotFound, nil) }
            entries[account] = data; return (errSecSuccess, nil)
        case .read:
            if let account = account { return entries[account].map { (errSecSuccess, $0) } ?? (errSecItemNotFound, nil) }
            return (errSecSuccess, entries.keys.map { [kSecAttrAccount as String: $0] })
        case .delete:
            guard let account = account, entries.removeValue(forKey: account) != nil else { return (errSecItemNotFound, nil) }
            return (errSecSuccess, nil)
        }
    }
}

@MainActor private final class FixtureVPN: VPNEntry {
    var provider: String?
    var configuration: [String: Any]?
    var status: NEVPNStatus = .disconnected
    var failure = ""
    var starts = 0
    var stops = 0
    var saves = 0
    var reloads = 0
    var update: (() -> Void)?
    var saving: (() -> Void)?
    var reloading: (() -> Void)?
    var saved: CheckedContinuation<Void, Never>?
    func configure(_ handoff: Handoff, provider: String) { self.provider = provider; configuration = handoff.configuration }
    func save() async throws {
        saves += 1
        if failure == "save" { throw NSError(domain: NEVPNErrorDomain, code: NEVPNError.configurationReadWriteFailed.rawValue) }
        if let saving = saving { await withCheckedContinuation { saved = $0; saving() } }
    }
    func reload() async throws {
        reloads += 1; reloading?()
        if failure == "reload" { throw SafeFailure(message: "reload rejected") }
    }
    func start() throws { if failure == "start" { throw SafeFailure(message: "permission/start rejected") }; starts += 1 }
    func stop() { stops += 1; status = .disconnected; update?() }
    func observe(_ update: @escaping () -> Void) { self.update = update }
    func lastError() async -> Error? { BridgeFailure(code: -6) }
}

@MainActor private final class FixturePreferences: VPNPreferences {
    var entries: [FixtureVPN] = []
    var loadFailure = false
    func load() async throws -> [VPNEntry] { if loadFailure { throw SafeFailure(message: "load rejected") }; return entries }
    func make() -> VPNEntry { let entry = FixtureVPN(); entries.append(entry); return entry }
}

enum DevelopmentTests {
    static func rejects(_ operation: () throws -> Void, _ name: String) throws {
        do { try operation() } catch { return }
        throw NSError(domain: "isolated.\(name)", code: 1)
    }
    static func terminal(_ native: NativeSession) throws {
        let deadline = Date().addingTimeInterval(3)
        while (native.state == 1 || native.state == 2) && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
        try SelfTests.require(native.state == 4 || native.state < 0, "native-terminal")
    }
    static func startup() throws {
        let native = try NativeSession(mode: 1); try SelfTests.ready(native)
        let control = DispatchQueue(label: "fixture.control"), worker = DispatchQueue(label: "fixture.worker")
        worker.suspend()
        let bridge = PacketBridge(native: native, control: control, worker: worker)
        let done = DispatchSemaphore(value: 0), stopped = DispatchSemaphore(value: 0)
        let flow = FixtureFlow()
        var configured = false, error: Error?
        bridge.start(flow: flow, configure: { configured = true; $0(nil) }, completion: { error = $0; done.signal() }, failed: { _ in })
        control.sync {}; control.suspend(); worker.resume(); worker.sync {}
        native.cancel()
        do { try terminal(native) } catch { control.resume(); throw error }
        control.resume(); try SelfTests.wait(done)
        bridge.stop { stopped.signal() }; try SelfTests.wait(stopped)
        try SelfTests.require(error != nil && !configured && flow.reads == 0, "stale-worker-ready-rejected")
        let failed = PacketBridge(native: try NativeSession(mode: 1))
        let failedFlow = FixtureFlow()
        failed.start(flow: failedFlow, configure: { $0(BridgeFailure(code: -71)); $0(nil) }, completion: { error = $0; done.signal() }, failed: { _ in })
        try SelfTests.wait(done); failed.stop { stopped.signal() }; try SelfTests.wait(stopped)
        try SelfTests.require((error as? BridgeFailure)?.code == -71 && failedFlow.reads == 0, "network-settings-error-preserved")
        try SelfTests.require(done.wait(timeout: .now() + 0.05) == .timedOut && fc_ios_handles() == 0, "configure-double-callback-cleanup")
    }
    static func provider() throws {
        let owner = ProviderLifecycle(), path = FixturePath(), flow = FixtureFlow()
        let entered = DispatchSemaphore(value: 0), completed = DispatchSemaphore(value: 0), stopped = DispatchSemaphore(value: 0)
        var configureReply: ((Error?) -> Void)?, error: Error?
        var native: NativeSession?
        let rejectedPath = FixturePath()
        owner.start(flow: flow, watcher: rejectedPath, makeNative: { _ in throw BridgeFailure(code: -81) }, configure: { $0(nil) },
                    completion: { error = $0; completed.signal() }, failed: { _ in completed.signal() })
        try SelfTests.wait(completed)
        try SelfTests.require((error as? BridgeFailure)?.code == -81 && rejectedPath.stopped && fc_ios_handles() == 0, "provider-material-failure-cleans")
        owner.start(flow: flow, watcher: path, makeNative: { _ in let session = try NativeSession(mode: 1); native = session; return session },
                    configure: { configureReply = $0; entered.signal() }, completion: { error = $0; completed.signal() }, failed: { _ in completed.signal() })
        try SelfTests.wait(entered)
        native?.cancel(); try terminal(native!)
        configureReply?(nil); try SelfTests.wait(completed)
        try SelfTests.require(error != nil && path.stopped && flow.reads == 0 && fc_ios_handles() == 0, "provider-error-cleans-before-reply")
        let second = FixturePath()
        owner.start(flow: flow, watcher: second, makeNative: { _ in try NativeSession(mode: 1) },
                    configure: { configureReply = $0; entered.signal() }, completion: { error = $0; completed.signal() }, failed: { _ in completed.signal() })
        try SelfTests.wait(entered)
        owner.stop { stopped.signal() }; try SelfTests.wait(stopped); try SelfTests.wait(completed)
        try SelfTests.require(fc_ios_handles() == 0 && second.stopped, "provider-stop-joins")
        owner.start(flow: flow, watcher: FixturePath(), makeNative: { _ in try NativeSession(mode: 1) }, configure: { $0(nil) },
                    completion: { error = $0; completed.signal() }, failed: { _ in })
        try SelfTests.wait(completed); try SelfTests.require(error != nil, "pending-settings-prevents-overlap")
        configureReply?(nil)
        owner.start(flow: flow, watcher: FixturePath(), makeNative: { _ in try NativeSession(mode: 1) }, configure: { $0(nil) },
                    completion: { error = $0; completed.signal() }, failed: { _ in completed.signal() })
        try SelfTests.wait(completed); try SelfTests.require(error == nil, "provider-recreated-after-callback")
        path.callback?(nil); second.callback?(nil); configureReply?(BridgeFailure(code: -71))
        try SelfTests.require(completed.wait(timeout: .now() + 0.05) == .timedOut, "old-generation-ignored")
        owner.stop { stopped.signal() }; try SelfTests.wait(stopped)
        try SelfTests.require(fc_ios_handles() == 0, "provider-final-cleanup")
    }
    private static func vault(_ driver: FixtureKeychain) throws -> MaterialStore {
        try MaterialStore(group: "TESTTEAM01.org.familyconnect.fixture.materials", service: "org.familyconnect.fixture.materials", driver: driver,
                          validate: { data in guard (try? JSONDecoder().decode(ImportedMaterial.self, from: data))?.version == 1 else { throw SafeFailure(message: "synthetic schema rejected") } })
    }
    private static func synthetic() throws -> Data {
        try JSONEncoder().encode(ImportedMaterial(version: 1, profile: Data("synthetic-not-credentials".utf8), directory: Data("synthetic-not-directory".utf8), resolver: "192.0.2.1:53"))
    }
    static func material() throws {
        try SelfTests.require((BridgeFailure(code: -6) as NSError).code == -6, "transport-error-survives-NSError")
        let driver = FixtureKeychain(), store = try vault(driver)
        let reference = try store.insert(synthetic())
        try SelfTests.require(driver.last[kSecAttrAccessible as String] as? String == kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly as String, "keychain-after-first-unlock-device-only")
        try SelfTests.require(driver.last[kSecAttrAccessGroup as String] as? String == "TESTTEAM01.org.familyconnect.fixture.materials", "keychain-specific-group")
        _ = try store.load(reference)
        let handoff = try Handoff(reference: reference, identifier: UUID().uuidString)
        try SelfTests.require(Set(handoff.configuration.keys) == Set(["version", "materialReference", "configurationID"]), "opaque-preferences-only")
        try rejects({ _ = try Handoff(configuration: ["profile": Data()]) }, "reject-legacy-cleartext")
        try rejects({ try ImportedMaterial.validate(try synthetic()) }, "real-native-rejects-synthetic-wrapper-fixture")
        try rejects({ _ = try store.insert(Data(repeating: 0, count: 96 * 1024 + 1)) }, "size-limit")
        for code in [errSecItemNotFound, errSecInteractionNotAllowed, errSecNotAvailable, errSecMissingEntitlement] {
            driver.failure = code; try rejects({ _ = try store.load(reference) }, "keychain-fails-closed")
        }
        driver.failure = nil
        try store.revoke(reference); try rejects({ _ = try store.load(reference) }, "revoked-reference")
        let replacement = try store.insert(synthetic())
        try SelfTests.require(replacement != reference, "immutable-replacement")
        driver.entries[replacement] = Data("corrupt".utf8)
        try rejects({ _ = try store.load(replacement) }, "corrupt-keychain-record")
        try store.delete(replacement); try rejects({ _ = try store.load(replacement) }, "deleted-reference")
        try rejects({ _ = try store.load("not-a-reference") }, "invalid-reference")
    }
    static func manager() throws {
        let done = DispatchSemaphore(value: 0)
        var failure: Error?
        Task { @MainActor in
            do { try await managerModel() } catch { failure = error }
            done.signal()
        }
        try SelfTests.wait(done)
        if let failure = failure { throw failure }
    }
    @MainActor private static func managerModel() async throws {
        let preferences = FixturePreferences(), store = try vault(FixtureKeychain())
        let reference = try store.insert(synthetic())
        func controller() -> VPNController { VPNController(preferences: preferences, provider: "org.familyconnect.fixture.tunnel", store: { store }) }
        let first = controller(); first.selectedReference = reference
        await first.prepare(connect: false)
        try SelfTests.require(preferences.entries.count == 1, "manager-create-once")
        let entry = preferences.entries[0]
        let reopened = controller(); await reopened.refresh()
        await reopened.prepare(connect: true); await reopened.prepare(connect: true)
        try SelfTests.require(preferences.entries.count == 1 && entry.starts == 1 && entry.reloads == 2, "reload-before-start-idempotent-connect")
        try SelfTests.require(reopened.status == .disconnected, "start-return-not-connected")
        entry.status = .connecting; entry.update?(); try SelfTests.require(reopened.status == .connecting, "system-status-notification")
        entry.status = .connected; entry.update?(); try SelfTests.require(reopened.status == .connected, "system-connected-observed")
        reopened.disconnect()
        for stage in ["save", "reload", "start"] {
            entry.failure = stage; await reopened.prepare(connect: true)
            try SelfTests.require(entry.starts == 1 && !reopened.busy, "save-reload-permission-error-no-start")
            try SelfTests.require(reopened.message.lowercased().contains(stage), "operation-error-context")
        }
        entry.failure = ""
        entry.saving = { reopened.disconnect(); entry.saved?.resume(); entry.saved = nil }
        await reopened.prepare(connect: true)
        try SelfTests.require(entry.starts == 1, "disconnect-during-save-cancels-start")
        entry.saving = nil
        entry.reloading = { reopened.disconnect() }
        await reopened.prepare(connect: true)
        try SelfTests.require(entry.starts == 1, "disconnect-during-reload-cancels-start")
        entry.reloading = nil
        preferences.loadFailure = true; await reopened.prepare(connect: true)
        try SelfTests.require(entry.starts == 1, "load-failure-no-start"); preferences.loadFailure = false
        try store.delete(reference); await reopened.prepare(connect: true)
        try SelfTests.require(entry.starts == 1, "missing-material-no-start")
        let duplicate = FixtureVPN(); duplicate.configuration = entry.configuration; duplicate.provider = entry.provider
        preferences.entries.append(duplicate); await reopened.refresh()
        try SelfTests.require(reopened.message.contains("Duplicate"), "duplicate-id-fails-without-bulk-delete")
    }
}
