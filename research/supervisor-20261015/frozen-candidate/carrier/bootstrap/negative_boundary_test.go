package bootstrap

import (
	"context"
	"encoding/json"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func TestNegativeAuthMandatoryRejectionBoundary(test *testing.T) {
	path := gatewayProfile(test)
	for _, name := range []string{"valid", "unknown", "wrong-family", "revoked", "wrong-gateway", "stale-crl", "stale-revision"} {
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			var calls, admissions atomic.Int32
			var mutex sync.Mutex
			var reports []ExchangeFailure
			broker, _ := testBroker(test, &calls, nil, "")
			client, server := pair()
			finished := make(chan error, 1)
			go func() {
				finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
					OpenServer(ctx, endpoint, path, broker, func(event string) {
						if event == "bootstrap_family_auth" {
							admissions.Add(1)
						}
					}, func(failure ExchangeFailure) {
						mutex.Lock()
						reports = append(reports, failure)
						mutex.Unlock()
					})
				})
			}()
			profileName := name
			if strings.HasPrefix(name, "stale-") || name == "wrong-gateway" {
				profileName = "valid"
			}
			raw := fixture(test, profileName)
			if profileName != name {
				var credentials familysession.Credentials
				if json.Unmarshal(raw, &credentials) != nil {
					test.Fatal("invalid disposable fixture")
				}
				switch name {
				case "wrong-gateway":
					credentials.Gateway = strings.Repeat("0", 32)
				case "stale-crl":
					credentials.MinimumCRL = 999
				case "stale-revision":
					credentials.MinimumRevision = 999
				}
				raw = encode(credentials)
			}
			descriptor, err := recoverCarrier(ctx, client, raw, func(string) {})
			cancel()
			<-finished
			if name == "valid" {
				if err != nil || descriptor.SetupID == "" || calls.Load() != 1 || admissions.Load() != 1 {
					test.Fatal("valid control did not establish authenticated handoff")
				}
			} else if err == nil || descriptor.SetupID != "" || calls.Load() != 0 || admissions.Load() != 0 {
				test.Fatal("mandatory rejection failed")
			}
			mutex.Lock()
			defer mutex.Unlock()
			test.Logf("case=%s rejected=%t descriptor_present=%t provider_calls=%d authenticated=%d diagnostic_reports=%v", name, err != nil, descriptor.SetupID != "", calls.Load(), admissions.Load(), reports)
		})
	}
}
