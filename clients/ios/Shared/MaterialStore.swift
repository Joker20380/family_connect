import Foundation
import Security

struct SafeFailure: Error, LocalizedError, CustomStringConvertible, CustomNSError {
    let message: String
    var errorDescription: String? { message }
    var description: String { message }
    static var errorDomain: String { "org.familyconnect.mesh.safe" }
    var errorCode: Int { 1 }
    var errorUserInfo: [String: Any] { [NSLocalizedDescriptionKey: message] }
}

func safeMessage(_ error: Error) -> String {
    if let error = error as? SafeFailure { return error.message }
    if let error = error as? BridgeFailure { return error.description }
    let system = error as NSError
    if system.domain == SafeFailure.errorDomain { return system.localizedDescription }
    if system.domain == BridgeFailure.errorDomain, let code = Int32(exactly: system.code) { return BridgeFailure(code: code).description }
    return "System operation failed (code \((error as NSError).code)); no material is logged."
}

struct ImportedMaterial: Codable {
    let version: Int
    let profile: Data
    let directory: Data
    let resolver: String

    static func validate(_ data: Data) throws {
        guard !data.isEmpty && data.count <= 96 * 1024 else { throw SafeFailure(message: "Import size rejected") }
        guard let decoded = try? JSONDecoder().decode(ImportedMaterial.self, from: data), decoded.version == 1 else {
            throw SafeFailure(message: "Import format/version rejected by Swift decoder")
        }
        let code = data.withUnsafeBytes { fc_ios_validate_material(UnsafeMutableRawPointer(mutating: $0.baseAddress), Int32($0.count)) }
        guard code == 0 else { throw SafeFailure(message: "Material format, version, trust, revocation or expiry rejected") }
    }
    func nativeData(interface: String) throws -> Data {
        try JSONSerialization.data(withJSONObject: ["profile": profile.base64EncodedString(),
            "directory": directory.base64EncodedString(), "resolver": resolver, "interface": interface])
    }
}

enum KeychainOperation: Equatable { case add, read, update, delete }
protocol KeychainDriver {
    func perform(_ operation: KeychainOperation, query: [String: Any]) -> (OSStatus, Any?)
}

struct SystemKeychain: KeychainDriver {
    func perform(_ operation: KeychainOperation, query: [String: Any]) -> (OSStatus, Any?) {
        var result: CFTypeRef?
        switch operation {
        case .add: return (SecItemAdd(query as CFDictionary, nil), nil)
        case .read:
            let code = SecItemCopyMatching(query as CFDictionary, &result)
            return (code, result)
        case .update:
            var selection = query
            let data = selection.removeValue(forKey: kSecValueData as String)!
            return (SecItemUpdate(selection as CFDictionary, [kSecValueData as String: data] as CFDictionary), nil)
        case .delete: return (SecItemDelete(query as CFDictionary), nil)
        }
    }
}

final class MaterialStore {
    private struct Record: Codable { let version: Int; let revoked: Bool; let material: Data? }
    private let group: String
    private let service: String
    private let driver: KeychainDriver
    private let validate: (Data) throws -> Void

    init(group: String, service: String, driver: KeychainDriver = SystemKeychain(),
         validate: @escaping (Data) throws -> Void = ImportedMaterial.validate) throws {
        guard !group.isEmpty, !group.contains("$("), group.hasSuffix("." + service),
              !group.contains("com.apple.managed"), !service.hasPrefix("com.apple.") else {
            throw SafeFailure(message: "App-specific Keychain group is not configured")
        }
        self.group = group; self.service = service; self.driver = driver; self.validate = validate
    }
    static func configured() throws -> MaterialStore {
        guard let group = Bundle.main.object(forInfoDictionaryKey: "FCKeychainGroup") as? String,
              let service = Bundle.main.object(forInfoDictionaryKey: "FCMaterialService") as? String else {
            throw SafeFailure(message: "Keychain build settings missing")
        }
        return try MaterialStore(group: group, service: service)
    }
    private func query(_ reference: String? = nil) throws -> [String: Any] {
        var query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service, kSecAttrAccessGroup as String: group,
            kSecAttrSynchronizable as String: false]
        if let reference = reference {
            guard UUID(uuidString: reference)?.uuidString == reference else { throw SafeFailure(message: "Invalid material reference") }
            query[kSecAttrAccount as String] = reference
        }
        return query
    }
    private func check(_ status: OSStatus) throws {
        if status == errSecSuccess { return }
        if status == errSecItemNotFound { throw SafeFailure(message: "Material item is missing or was deleted; re-import explicitly") }
        if status == errSecInteractionNotAllowed || status == errSecNotAvailable {
            throw SafeFailure(message: "Keychain unavailable; unlock once after reboot and try again")
        }
        if status == errSecMissingEntitlement { throw SafeFailure(message: "Keychain entitlement/group unavailable; verify provisioning") }
        throw SafeFailure(message: "Keychain operation failed (code \(status))")
    }
    func references() throws -> [String] {
        var selection = try query()
        selection[kSecReturnAttributes as String] = true
        selection[kSecMatchLimit as String] = kSecMatchLimitAll
        let (status, result) = driver.perform(.read, query: selection)
        if status == errSecItemNotFound { return [] }
        try check(status)
        guard let rows = result as? [[String: Any]] else { throw SafeFailure(message: "Keychain metadata corrupt") }
        return rows.compactMap { $0[kSecAttrAccount as String] as? String }.filter { UUID(uuidString: $0)?.uuidString == $0 }.sorted()
    }
    func insert(_ data: Data) throws -> String {
        guard data.count <= 96 * 1024 else { throw SafeFailure(message: "Import size rejected") }
        try validate(data)
        let reference = UUID().uuidString
        var entry = try query(reference)
        entry[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        entry[kSecValueData as String] = try JSONEncoder().encode(Record(version: 1, revoked: false, material: data))
        try check(driver.perform(.add, query: entry).0)
        return reference
    }
    func load(_ reference: String) throws -> ImportedMaterial {
        var selection = try query(reference)
        selection[kSecReturnData as String] = true
        selection[kSecMatchLimit as String] = kSecMatchLimitOne
        let (status, result) = driver.perform(.read, query: selection)
        try check(status)
        guard let data = result as? Data, data.count <= 132 * 1024,
              let record = try? JSONDecoder().decode(Record.self, from: data), record.version == 1 else {
            throw SafeFailure(message: "Keychain material record corrupt")
        }
        guard !record.revoked else { throw SafeFailure(message: "Material reference was revoked; re-import explicitly") }
        guard let material = record.material, material.count <= 96 * 1024 else { throw SafeFailure(message: "Keychain material record corrupt") }
        try validate(material)
        guard let decoded = try? JSONDecoder().decode(ImportedMaterial.self, from: material) else { throw SafeFailure(message: "Keychain material format corrupt") }
        return decoded
    }
    func revoke(_ reference: String) throws {
        var entry = try query(reference)
        entry[kSecValueData as String] = try JSONEncoder().encode(Record(version: 1, revoked: true, material: nil))
        try check(driver.perform(.update, query: entry).0)
    }
    func delete(_ reference: String) throws { try check(driver.perform(.delete, query: query(reference)).0) }
}

struct Handoff {
    let reference: String
    let identifier: String
    var configuration: [String: Any] { ["version": 1, "materialReference": reference, "configurationID": identifier] }
    init(reference: String, identifier: String) throws {
        guard UUID(uuidString: reference)?.uuidString == reference, UUID(uuidString: identifier)?.uuidString == identifier else {
            throw SafeFailure(message: "Invalid handoff identifier")
        }
        self.reference = reference; self.identifier = identifier
    }
    init(configuration: [String: Any]?) throws {
        guard let config = configuration, Set(config.keys) == Set(["version", "materialReference", "configurationID"]),
              config["version"] as? Int == 1, let reference = config["materialReference"] as? String,
              let identifier = config["configurationID"] as? String else { throw SafeFailure(message: "VPN handoff missing or unsupported") }
        try self.init(reference: reference, identifier: identifier)
    }
}
