package mixed

import "testing"

func TestGatewayInstalledOutboundStallDifferential(test *testing.T) {
    for _, gateway := range []string{"oldgateway", "candidate"} {
        test.Run(gateway, func(test *testing.T) {
            versions := struct{ name, client, gateway string }{"INSTALLED_STALL_DIFFERENTIAL", "oldclient", gateway}
            burstCase(test, versions, 16, true)
        })
    }
}
