package familysession

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"net"
	"testing"
	"time"
)

func TestMuxALPNProfiles(test *testing.T) {
	for _, scenario := range []struct {
		name           string
		client, server bool
		bad            string
		want           string
	}{
		{"legacy", false, false, "", Protocol}, {"new-old", true, false, "", Protocol},
		{"old-new", false, true, "", Protocol}, {"new-new", true, true, "", MuxCredit128Protocol},
		{"disabled", true, false, "", Protocol}, {"unknown", true, true, "unknown", ""},
		{"empty", true, true, "empty", ""}, {"no-common", true, false, "exclusive", ""},
		{"family", true, true, "family", ""}, {"crl-floor", true, true, "crl", ""},
		{"expired", true, true, "expired", ""},
	} {
		test.Run(scenario.name, func(test *testing.T) {
			client, server := profiles(test)
			if scenario.bad == "expired" {
				client, server = profilesWithExpiry(test, time.Now().Add(-time.Second))
			}
			if scenario.bad == "family" {
				client.Family = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
			}
			if scenario.bad == "crl" {
				client.MinimumCRL++
			}
			clientRaw, _ := json.Marshal(client)
			serverRaw, _ := json.Marshal(server)
			clientConfig, _, err := MuxConfiguration(clientRaw, false, scenario.client)
			if err != nil {
				if scenario.bad == "crl" {
					return
				}
				test.Fatal(err)
			}
			serverConfig, _, err := MuxConfiguration(serverRaw, true, scenario.server)
			if err != nil {
				test.Fatal(err)
			}
			if scenario.bad == "unknown" {
				clientConfig.NextProtos = []string{"unknown-profile"}
			}
			if scenario.bad == "empty" {
				clientConfig.NextProtos = nil
			}
			if scenario.bad == "exclusive" {
				clientConfig.NextProtos = []string{MuxCredit128Protocol}
			}
			left, right := net.Pipe()
			defer left.Close()
			defer right.Close()
			clientTLS, serverTLS := tls.Client(left, clientConfig), tls.Server(right, serverConfig)
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			completed := make(chan error, 1)
			go func() { completed <- serverTLS.HandshakeContext(ctx) }()
			clientErr := clientTLS.HandshakeContext(ctx)
			serverErr := <-completed
			if scenario.want == "" {
				if clientErr == nil && serverErr == nil {
					test.Fatal("unauthorized profile accepted")
				}
				return
			}
			if clientErr != nil || serverErr != nil {
				test.Fatal(clientErr, serverErr)
			}
			for _, connection := range []*tls.Conn{clientTLS, serverTLS} {
				if connection.ConnectionState().NegotiatedProtocol != scenario.want {
					test.Fatal("wrong negotiated profile")
				}
				session := &Session{connection: connection}
				window, err := session.MuxWindow()
				want := 65536
				if scenario.want == MuxCredit128Protocol {
					want = 131072
				}
				if err != nil || window != want {
					test.Fatal(window, err)
				}
			}
		})
	}
}

func TestMuxProfileUnknownSessionRejected(test *testing.T) {
	if _, err := (&Session{}).MuxWindow(); err == nil {
		test.Fatal("unverified session accepted")
	}
	client, _ := profiles(test)
	raw, _ := json.Marshal(client)
	config, _, err := Configuration(raw, false)
	if err != nil {
		test.Fatal(err)
	}
	if len(config.NextProtos) != 1 || config.NextProtos[0] != Protocol {
		test.Fatal("generic session gained Mux extension")
	}
}
