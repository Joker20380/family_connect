import Foundation
import Network
import NetworkExtension

final class PacketTunnelProvider: NEPacketTunnelProvider {
    private let lifecycle = DispatchQueue(label: "family.mesh.provider")
    private var bridge: PacketBridge?
    private var monitor: NWPathMonitor?
    private var startReply: ((Error?) -> Void)?
    private var selectedInterface: String?

    override func startTunnel(options: [String: NSObject]?, completionHandler: @escaping (Error?) -> Void) {
        lifecycle.async {
            guard self.startReply == nil && self.bridge == nil else { completionHandler(BridgeFailure(code: -1)); return }
            self.startReply = completionHandler
            guard let tunnelProtocol = self.protocolConfiguration as? NETunnelProviderProtocol,
                  !tunnelProtocol.includeAllNetworks, !tunnelProtocol.enforceRoutes else {
                self.finishStart(BridgeFailure(code: -8)); return
            }
            guard let config = tunnelProtocol.providerConfiguration,
                  let profile = config["profile"] as? Data, let directory = config["directory"] as? Data,
                  let resolver = config["resolver"] as? String else {
                self.finishStart(BridgeFailure(code: -1)); return
            }
            let monitor = NWPathMonitor()
            self.monitor = monitor
            monitor.pathUpdateHandler = { path in
                guard self.monitor === monitor else { return }
                guard path.status == .satisfied,
                      let interface = path.availableInterfaces.first(where: {
                          ($0.type == .wifi || $0.type == .cellular) && path.usesInterfaceType($0.type)
                      }) else { self.failPath(); return }
                if let selected = self.selectedInterface {
                    if selected != interface.name { self.failPath() }
                    return
                }
                self.selectedInterface = interface.name
                do {
                    let material: [String: Any] = ["profile": profile.base64EncodedString(),
                        "directory": directory.base64EncodedString(), "resolver": resolver, "interface": interface.name]
                    let native = try NativeSession(config: JSONSerialization.data(withJSONObject: material))
                    let bridge = PacketBridge(native: native)
                    self.bridge = bridge
                    bridge.start(flow: self.packetFlow, configure: { done in
                        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: "198.18.0.1")
                        let ipv4 = NEIPv4Settings(addresses: ["198.18.0.2"], subnetMasks: ["255.255.255.252"])
                        ipv4.includedRoutes = [NEIPv4Route.default()]
                        let ipv6 = NEIPv6Settings(addresses: ["fd00:fc::2"], networkPrefixLengths: [128])
                        ipv6.includedRoutes = [NEIPv6Route.default()]
                        settings.ipv4Settings = ipv4
                        settings.ipv6Settings = ipv6
                        settings.dnsSettings = NEDNSSettings(servers: ["198.18.0.1"])
                        settings.dnsSettings?.matchDomains = [""]
                        settings.mtu = 1280
                        self.setTunnelNetworkSettings(settings, completionHandler: done)
                    }, completion: { error in
                        self.lifecycle.async { self.finishStart(error) }
                    }, failed: { error in
                        self.lifecycle.async { self.stopMonitor(); self.cancelTunnelWithError(error) }
                    })
                } catch { self.finishStart(error) }
            }
            monitor.start(queue: self.lifecycle)
        }
    }

    private func finishStart(_ error: Error?) {
        let reply = startReply
        startReply = nil
        if error != nil { stopMonitor() }
        reply?(error)
    }

    private func failPath() {
        stopMonitor()
        if startReply != nil { finishStart(BridgeFailure(code: -8)) }
        bridge?.stop {}
        cancelTunnelWithError(BridgeFailure(code: -8))
    }

    private func stopMonitor() {
        monitor?.pathUpdateHandler = nil
        monitor?.cancel()
        monitor = nil
    }

    override func stopTunnel(with reason: NEProviderStopReason, completionHandler: @escaping () -> Void) {
        lifecycle.async {
            self.stopMonitor()
            self.selectedInterface = nil
            self.finishStart(BridgeFailure(code: -2))
            guard let bridge = self.bridge else { completionHandler(); return }
            self.bridge = nil
            bridge.stop(completion: completionHandler)
        }
    }
}
