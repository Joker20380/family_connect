import Foundation
import Network

protocol PathWatcher: AnyObject {
    func start(_ update: @escaping (String?) -> Void)
    func stop()
}

final class SystemPathWatcher: PathWatcher {
    private let monitor = NWPathMonitor()
    func start(_ update: @escaping (String?) -> Void) {
        monitor.pathUpdateHandler = { path in
            let interface = path.availableInterfaces.first {
                ($0.type == .wifi || $0.type == .cellular) && path.usesInterfaceType($0.type)
            }
            update(path.status == .satisfied ? interface?.name : nil)
        }
        monitor.start(queue: DispatchQueue(label: "family.mesh.path"))
    }
    func stop() { monitor.pathUpdateHandler = nil; monitor.cancel() }
}

final class ProviderLifecycle {
    private final class Run {
        let watcher: PathWatcher
        var bridge: PacketBridge?
        var native: NativeSession?
        var interface: String?
        var closing = false
        var startup: ((Error?) -> Void)?
        var failure: ((Error) -> Void)?
        var stops: [() -> Void] = []
        init(watcher: PathWatcher, completion: @escaping (Error?) -> Void, failed: @escaping (Error) -> Void) {
            self.watcher = watcher; startup = completion; failure = failed
        }
    }
    private let queue = DispatchQueue(label: "family.mesh.provider")
    private var current: Run?
    private var settingsPending = false

    func start(flow: PacketFlow, watcher: PathWatcher,
               makeNative: @escaping (String) throws -> NativeSession,
               configure: @escaping (@escaping (Error?) -> Void) -> Void,
               completion: @escaping (Error?) -> Void, failed: @escaping (Error) -> Void) {
        queue.async {
            guard self.current == nil && !self.settingsPending else {
                watcher.stop(); completion(SafeFailure(message: "Previous provider/settings operation has not finished")); return
            }
            let run = Run(watcher: watcher, completion: completion, failed: failed)
            self.current = run
            watcher.start { [weak self, weak run] interface in
                guard let self = self, let run = run else { return }
                self.queue.async {
                    guard self.current === run && !run.closing else { return }
                    guard let interface = interface else { self.close(run, error: BridgeFailure(code: -8)); return }
                    if let selected = run.interface {
                        if selected != interface { self.close(run, error: BridgeFailure(code: -8)) }
                        return
                    }
                    run.interface = interface
                    do {
                        let native = try makeNative(interface)
                        let bridge = PacketBridge(native: native)
                        run.native = native; run.bridge = bridge
                        bridge.start(flow: flow, configure: { [weak self, weak run] reply in
                            guard let self = self, let run = run else { reply(BridgeFailure(code: -2)); return }
                            self.queue.async {
                                guard self.current === run && !run.closing else { reply(BridgeFailure(code: -2)); return }
                                self.settingsPending = true
                                var answered = false
                                configure { error in
                                    self.queue.async {
                                        guard !answered else { return }
                                        answered = true; self.settingsPending = false
                                        reply(error)
                                    }
                                }
                            }
                        }, completion: { [weak self, weak run] error in
                            guard let self = self, let run = run else { return }
                            self.queue.async {
                                guard self.current === run && !run.closing else { return }
                                if let error = error { self.close(run, error: error); return }
                                let state = native.state
                                guard state == 2 else { self.close(run, error: BridgeFailure(code: state < 0 ? state : -2)); return }
                                let reply = run.startup; run.startup = nil; reply?(nil)
                            }
                        }, failed: { [weak self, weak run] error in
                            guard let self = self, let run = run else { return }
                            self.queue.async { self.close(run, error: error) }
                        })
                    } catch { self.close(run, error: error) }
                }
            }
            self.queue.asyncAfter(deadline: .now() + 10) { [weak run] in
                if let run = run, self.current === run && run.interface == nil {
                    self.close(run, error: SafeFailure(message: "No eligible underlay path within 10 seconds"))
                }
            }
        }
    }
    private func close(_ run: Run, error: Error?) {
        guard current === run && !run.closing else { return }
        run.closing = true; run.watcher.stop()
        let finish = {
            self.queue.async {
                guard self.current === run else { return }
                run.bridge = nil; run.native = nil; run.interface = nil
                let startup = run.startup; let failure = run.failure; let stops = run.stops
                run.startup = nil; run.failure = nil; run.stops = []
                self.current = nil
                if let startup = startup { startup(error ?? BridgeFailure(code: -2)) }
                else if let error = error { failure?(error) }
                for stop in stops { stop() }
            }
        }
        if let bridge = run.bridge { bridge.stop(completion: finish) } else { finish() }
    }
    func stop(completion: @escaping () -> Void) {
        queue.async {
            guard let run = self.current else { completion(); return }
            run.stops.append(completion)
            self.close(run, error: nil)
        }
    }
}
