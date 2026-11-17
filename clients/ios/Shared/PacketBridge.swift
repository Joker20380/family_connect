import Foundation
import NetworkExtension

struct BridgeFailure: Error, CustomStringConvertible {
    let code: Int32
    var description: String { "MESH bridge error \(code)" }
}

final class NativeSession {
    let handle: UInt64
    private let lock = NSLock()
    private var terminal: Int32?

    init(config: Data = Data(), mode: Int32 = 0) throws {
        handle = config.withUnsafeBytes {
            fc_ios_start(UnsafeMutableRawPointer(mutating: $0.baseAddress), Int32($0.count), mode)
        }
        guard handle != 0 else { throw BridgeFailure(code: -1) }
    }

    var state: Int32 {
        lock.lock(); defer { lock.unlock() }
        return terminal ?? fc_ios_state(handle)
    }
    func cancel() { fc_ios_cancel(handle) }
    func commitStart() -> Int32 { fc_ios_commit_start(handle) }
    func stop() {
        lock.lock(); defer { lock.unlock() }
        guard terminal == nil else { return }
        terminal = fc_ios_stop(handle)
    }
    deinit { stop() }

    func write(_ data: Data, family: Int32) -> Int32 {
        guard data.count <= 1280 else { return -1 }
        let version: Int32
        switch family {
        case AF_INET: version = 4
        case AF_INET6: version = 6
        default: return -1
        }
        return data.withUnsafeBytes {
            fc_ios_write(handle, UnsafeMutableRawPointer(mutating: $0.baseAddress), Int32($0.count), version)
        }
    }

    func read(wait: Int32 = 100) throws -> (Data, NSNumber)? {
        var bytes = [UInt8](repeating: 0, count: 1280)
        var version: Int32 = 0
        let count = fc_ios_read(handle, &bytes, 1280, &version, wait)
        if count == -5 { return nil }
        guard count > 0 && count <= 1280 && version == 4 else { throw BridgeFailure(code: count) }
        return (Data(bytes.prefix(Int(count))), NSNumber(value: AF_INET))
    }
}

protocol PacketFlow: AnyObject {
    func readPackets(completionHandler: @escaping ([Data], [NSNumber]) -> Void)
    func writePackets(_ packets: [Data], withProtocols protocols: [NSNumber]) -> Bool
}

extension NEPacketTunnelFlow: PacketFlow {}

final class PacketBridge {
    private let native: NativeSession
    private let control: DispatchQueue
    private let worker: DispatchQueue
    private var stopped = false
    private var started = false
    private var startup: ((Error?) -> Void)?
    private var failure: ((Error) -> Void)?
    private var dropped = 0

    init(native: NativeSession, control: DispatchQueue = DispatchQueue(label: "family.mesh.control"),
         worker: DispatchQueue = DispatchQueue(label: "family.mesh.receive")) {
        self.native = native; self.control = control; self.worker = worker
    }

    func start(flow: PacketFlow, configure: @escaping (@escaping (Error?) -> Void) -> Void,
               completion: @escaping (Error?) -> Void, failed: @escaping (Error) -> Void) {
        control.async {
            guard !self.started && !self.stopped else { completion(BridgeFailure(code: -2)); return }
            self.started = true
            self.startup = completion
            self.failure = failed
            self.worker.async {
                let deadline = Date().addingTimeInterval(180)
                while self.native.state == 1 && Date() < deadline { Thread.sleep(forTimeInterval: 0.01) }
                self.control.async {
                    guard !self.stopped else { return }
                    let state = self.native.state
                    guard state == 2 else { self.terminate(BridgeFailure(code: state == 1 ? -5 : state)); return }
                    configure { [weak self] error in
                        guard let self = self else { return }
                        self.control.async {
                            guard !self.stopped && self.startup != nil else { return }
                            if let error = error {
                                let state = self.native.state
                                self.terminate(state < 0 && state != -2 ? BridgeFailure(code: state) : error)
                                return
                            }
                            let admission = self.native.commitStart()
                            guard admission == 0 else { self.terminate(BridgeFailure(code: admission)); return }
                            self.finishStartup(nil)
                            self.readFlow(flow)
                            self.worker.async { self.receive(flow) }
                        }
                    }
                }
            }
        }
    }

    private func finishStartup(_ error: Error?) {
        let completion = startup
        startup = nil
        completion?(error)
    }

    private func terminate(_ error: Error) {
        guard !stopped else { return }
        stopped = true
        native.cancel()
        if startup != nil { finishStartup(error) } else { failure?(error) }
        failure = nil
        worker.async { self.native.stop() }
    }

    private func readFlow(_ flow: PacketFlow) {
        guard !stopped else { return }
        flow.readPackets { [weak self] packets, families in
            guard let self = self else { return }
            self.control.async {
                guard !self.stopped else { return }
                guard packets.count == families.count else { self.terminate(BridgeFailure(code: -1)); return }
                for (packet, family) in zip(packets, families) {
                    let code = self.native.write(packet, family: family.int32Value)
                    if code == -3 || code == -4 { self.dropped += 1 }
                    else if code != 0 { self.terminate(BridgeFailure(code: code)); return }
                }
                self.readFlow(flow)
            }
        }
    }

    private func receive(_ flow: PacketFlow) {
        do {
            while native.state == 2 {
                if let (packet, family) = try native.read() {
                    var accepted = true
                    control.sync {
                        if !self.stopped { accepted = flow.writePackets([packet], withProtocols: [family]) }
                    }
                    if !accepted { throw BridgeFailure(code: -7) }
                }
            }
            throw BridgeFailure(code: native.state)
        } catch {
            control.async { self.terminate(error) }
        }
    }

    func stop(completion: @escaping () -> Void) {
        control.async {
            self.stopped = true
            self.native.cancel()
            self.finishStartup(BridgeFailure(code: -2))
            self.failure = nil
            self.worker.async {
                self.native.stop()
                completion()
            }
        }
    }
}
