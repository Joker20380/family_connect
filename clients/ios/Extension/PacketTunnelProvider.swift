import Foundation
import NetworkExtension

final class PacketTunnelProvider: NEPacketTunnelProvider {
    private let lifecycle = ProviderLifecycle()

    override func startTunnel(options: [String: NSObject]?, completionHandler: @escaping (Error?) -> Void) {
        do {
            guard let tunnelProtocol = protocolConfiguration as? NETunnelProviderProtocol,
                  !tunnelProtocol.includeAllNetworks, !tunnelProtocol.enforceRoutes else {
                throw BridgeFailure(code: -8)
            }
            let handoff = try Handoff(configuration: tunnelProtocol.providerConfiguration)
            let store = try MaterialStore.configured()
            lifecycle.start(flow: packetFlow, watcher: SystemPathWatcher(), makeNative: { interface in
                let material = try store.load(handoff.reference)
                return try NativeSession(config: material.nativeData(interface: interface))
            }, configure: { [weak self] done in
                guard let self = self else { done(BridgeFailure(code: -2)); return }
                let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: "198.18.0.1")
                let ipv4 = NEIPv4Settings(addresses: ["198.18.0.2"], subnetMasks: ["255.255.255.252"])
                ipv4.includedRoutes = [NEIPv4Route.default()]
                let ipv6 = NEIPv6Settings(addresses: ["fd00:fc::2"], networkPrefixLengths: [128])
                ipv6.includedRoutes = [NEIPv6Route.default()]
                settings.ipv4Settings = ipv4; settings.ipv6Settings = ipv6
                settings.dnsSettings = NEDNSSettings(servers: ["198.18.0.1"])
                settings.dnsSettings?.matchDomains = [""]
                settings.mtu = 1280
                self.setTunnelNetworkSettings(settings, completionHandler: done)
            }, completion: completionHandler, failed: { [weak self] error in self?.cancelTunnelWithError(error) })
        } catch { completionHandler(error) }
    }

    override func stopTunnel(with reason: NEProviderStopReason, completionHandler: @escaping () -> Void) {
        lifecycle.stop(completion: completionHandler)
    }
}
