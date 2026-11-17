import Foundation

final class FixtureFlow: PacketFlow {
    private let lock = NSLock()
    private var callback: (([Data], [NSNumber]) -> Void)?
    private(set) var received: [(Data, NSNumber)] = []
    let written = DispatchSemaphore(value: 0)
    var acceptWrites = true

    func readPackets(completionHandler: @escaping ([Data], [NSNumber]) -> Void) {
        lock.lock(); callback = completionHandler; lock.unlock()
    }
    func writePackets(_ packets: [Data], withProtocols protocols: [NSNumber]) -> Bool {
        lock.lock()
        received += Array(zip(packets, protocols))
        let accepted = acceptWrites
        lock.unlock()
        written.signal()
        return accepted
    }
    func deliver(_ data: Data) -> Bool {
        lock.lock(); let ready = callback; callback = nil; lock.unlock()
        ready?([data], [NSNumber(value: AF_INET)])
        return ready != nil
    }
}

enum SelfTests {
    static func require(_ condition: @autoclosure () -> Bool, _ name: String) throws {
        if !condition() { throw NSError(domain: "isolated.\(name)", code: 1) }
    }
    static func wait(_ semaphore: DispatchSemaphore) throws {
        try require(semaphore.wait(timeout: .now() + 4) == .success, "bounded-wait")
    }
    static func ready(_ native: NativeSession) throws {
        let deadline = Date().addingTimeInterval(3)
        while native.state == 1 && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
        try require(native.state == 2, "native-ready")
    }
    static func packet() -> Data {
        var bytes = [UInt8](repeating: 0, count: 40)
        bytes.replaceSubrange(0..<10, with: [0x45, 0, 0, 40, 0, 1, 0, 0, 64, 17])
        bytes.replaceSubrange(12..<20, with: [198, 18, 0, 2, 198, 18, 0, 1])
        bytes.replaceSubrange(20..<30, with: [0xc0, 0, 0, 53, 0, 20, 0, 0, 0x12, 0x34])
        var checksum: UInt32 = 0
        for offset in stride(from: 0, to: 20, by: 2) { checksum += UInt32(bytes[offset]) << 8 | UInt32(bytes[offset+1]) }
        while checksum > 65535 { checksum = (checksum & 65535) + (checksum >> 16) }
        let value = ~UInt16(checksum)
        bytes[10] = UInt8(value >> 8); bytes[11] = UInt8(value & 255)
        return Data(bytes)
    }

    static func nativeBoundary() throws {
        let pending = try NativeSession(mode: 2)
        defer { pending.stop() }
        for _ in 0..<64 { try require(pending.write(packet(), family: AF_INET) == 0, "queue-admission") }
        try require(pending.write(packet(), family: AF_INET) == -3, "queue-full")
        pending.cancel()
        pending.stop()
        try require(pending.state == -2, "removed-handle")
        let denied = try NativeSession(config: Data("{}".utf8))
        defer { denied.stop() }
        let deadline = Date().addingTimeInterval(3)
        while denied.state == 1 && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
        try require(denied.state == -8, "no-fake-underlay-ready")
        for _ in 0..<8 {
            let native = try NativeSession(mode: 1)
            defer { native.stop() }
            try ready(native)
            var data = packet()
            try require(native.write(data, family: AF_INET) == 0, "write")
            data.resetBytes(in: 0..<data.count)
            guard let (answer, family) = try native.read(wait: 1000) else { throw BridgeFailure(code: -5) }
            try require(answer.count == 40 && answer[28] == 0x12 && answer[29] == 0x34 && answer[30] & 0x80 != 0, "real-dns-copy")
            try require(family.int32Value == AF_INET && Array(answer[12..<20]) == [198,18,0,1,198,18,0,2], "response-family-address")
            try require(native.write(packet(), family: AF_INET6) == -1, "mismatched-family")
            var ipv6 = Data(repeating: 0, count: 40); ipv6[0] = 0x60
            try require(native.write(ipv6, family: AF_INET6) == -4, "ipv6-denied")
            native.cancel()
            do { _ = try native.read(); throw NSError(domain: "read-not-cancelled", code: 1) }
            catch let error as BridgeFailure { try require(error.code == -2, "cancelled-read") }
            native.stop()
        }
    }

    static func packetFlowBoundary() throws {
        let flow = FixtureFlow()
        let bridge = PacketBridge(native: try NativeSession(mode: 1))
        let started = DispatchSemaphore(value: 0)
        let stopped = DispatchSemaphore(value: 0)
        let failed = DispatchSemaphore(value: 0)
        var startupError: Error?
        bridge.start(flow: flow, configure: { $0(nil) }, completion: { startupError = $0; started.signal() }, failed: { _ in failed.signal() })
        try wait(started)
        try require(startupError == nil, "pump-start")
        let deadline = Date().addingTimeInterval(2)
        while !flow.deliver(packet()) && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
        try wait(flow.written)
        try require(flow.received.first?.1.int32Value == AF_INET, "flow-protocol")
        bridge.stop { stopped.signal() }
        try wait(stopped)
        _ = flow.deliver(packet())
        try require(flow.written.wait(timeout: .now() + 0.05) == .timedOut, "late-flow-callback")
        try require(failed.wait(timeout: .now() + 0.05) == .timedOut, "stop-not-failure")
    }

    static func cancelConfiguration() throws {
        let bridge = PacketBridge(native: try NativeSession(mode: 1))
        let configuring = DispatchSemaphore(value: 0)
        let completed = DispatchSemaphore(value: 0)
        let stopped = DispatchSemaphore(value: 0)
        var configureReply: ((Error?) -> Void)?
        var startupError: Error?
        bridge.start(flow: FixtureFlow(), configure: { configureReply = $0; configuring.signal() },
                     completion: { startupError = $0; completed.signal() }, failed: { _ in })
        try wait(configuring)
        bridge.stop { stopped.signal() }
        try wait(completed); try wait(stopped)
        try require(startupError != nil, "cancel-config-not-ready")
        configureReply?(nil)
        try require(completed.wait(timeout: .now() + 0.05) == .timedOut, "exactly-once-start")
    }

    static func writeFailure() throws {
        let flow = FixtureFlow(); flow.acceptWrites = false
        let bridge = PacketBridge(native: try NativeSession(mode: 1))
        let started = DispatchSemaphore(value: 0)
        let failed = DispatchSemaphore(value: 0)
        let stopped = DispatchSemaphore(value: 0)
        bridge.start(flow: flow, configure: { $0(nil) }, completion: { _ in started.signal() }, failed: { _ in failed.signal() })
        try wait(started)
        let deadline = Date().addingTimeInterval(2)
        while !flow.deliver(packet()) && Date() < deadline { Thread.sleep(forTimeInterval: 0.005) }
        try wait(failed)
        bridge.stop { stopped.signal() }; try wait(stopped)
    }

    static func run() -> [String: Any] {
        var completed: [String] = []
        do {
            try nativeBoundary(); completed.append("Swift-C-Go-copy-family-queue-cancel-recreate")
            try packetFlowBoundary(); completed.append("async-flow-real-gvisor-wholedevice-DNS")
            try cancelConfiguration(); completed.append("cancel-config-late-completion")
            try writeFailure(); completed.append("write-error-propagation")
            try require(fc_ios_handles() == 0, "handle-release")
            return ["passed": true, "checks": completed, "handles": fc_ios_handles(), "scope": "isolated-not-system-TUN-or-Telemost"]
        } catch {
            return ["passed": false, "checks": completed, "error": String(describing: error), "handles": fc_ios_handles()]
        }
    }
}
