package materials

import (
	"context"
	"encoding/json"
	"net"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
)

func TestMaterialsPreservesAvailabilityCauseAndImportResult(test *testing.T) {
	for _, code := range []string{"CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE", "FETCH_NETWORK_FAILURE", "FETCH_TEMPORARY_SERVER_FAILURE", "RNS_UNAVAILABLE", "RNS_WORKER_UNAVAILABLE", "RNS_PROTOCOL_REJECTED", "TLS_TRUST_REJECTED", "FETCH_INCOMPATIBLE_RESPONSE"} {
		test.Run(code, func(test *testing.T) {
			command := refreshCommand()
			closed, calls := false, 0
			environment := preparationEnvironment{lookup: func(int) (*net.Interface, error) {
				return &net.Interface{Index: 2, Name: "synthetic", Flags: net.FlagUp}, nil
			}, open: func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error) {
				return testPost(func(context.Context, string, []byte, string) ([]byte, error) {
					calls++
					return nil, &desktopmesh.ReadinessFailure{Code: code, Availability: code != "TLS_TRUST_REJECTED" && code != "FETCH_INCOMPATIBLE_RESPONSE" && code != "RNS_PROTOCOL_REJECTED"}
				}), func() { closed = true }, nil
			}}
			before := time.Now().Unix()
			response := prepare(context.Background(), &command, &neverProtect{}, environment)
			if response.Code != code || response.ImportResult != "FETCH_FAILED" || response.OK || response.Validated || response.Durable || !response.StorageRequired || !closed || calls != 1 {
				test.Fatalf("materials cause/import collapsed: code=%s import=%s", response.Code, response.ImportResult)
			}
			var stored struct {
				NextAttempt int64 `json:"next_attempt"`
			}
			if json.Unmarshal(response.CacheProposal, &stored) != nil || stored.NextAttempt < before+300 || stored.NextAttempt > time.Now().Unix()+300 {
				test.Fatal("cooldown proposal missing")
			}
			command = receiptCommand()
			command.ImportResult = response.ImportResult
			command.Phase = "import"
			command.AppVersion = "test"
			command.VersionCode = 1
			receipt := prepare(context.Background(), &command, &neverProtect{}, environment)
			if !receipt.OK || receipt.Receipt == nil || receipt.Receipt.Result != "FETCH_FAILED" || calls != 1 {
				test.Fatal("failure receipt confused typed cause with import result")
			}
		})
	}
}
