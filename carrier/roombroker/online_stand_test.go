package roombroker

import (
	"bytes"
	"context"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"golang.org/x/net/dns/dnsmessage"
)

func standDelivery(test *testing.T, path string) []byte {
	test.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		test.Fatal(err)
	}
	defer clear(raw)
	command := exec.Command(os.Getenv("FC_DELIVERY_HELPER"))
	command.Stdin = bytes.NewReader(raw)
	profile, err := command.Output()
	if err != nil {
		test.Fatal("readiness validation", err)
	}
	return profile
}

func standReceipt(test *testing.T, root, name string, value any) {
	test.Helper()
	raw, err := json.Marshal(value)
	if err != nil {
		test.Fatal(err)
	}
	path := filepath.Join(root, name+".json")
	if err := os.WriteFile(path+".tmp", raw, 0600); err != nil {
		test.Fatal(err)
	}
	if err := os.Rename(path+".tmp", path); err != nil {
		test.Fatal(err)
	}
}

func TestOnlinePublicationStand(test *testing.T) {
	root := os.Getenv("FC_ONLINE_STAND")
	if root == "" {
		test.Skip("explicit isolated publication stand required")
	}
	dns := renewalDNS(test)
	origin := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) { io.WriteString(writer, "verified-isolated-origin") }))
	test.Cleanup(origin.Close)
	for _, slot := range []string{"NL", "NL2"} {
		test.Run(slot, func(test *testing.T) {
			test.Parallel()
			deliveryPath := filepath.Join(root, slot+"-delivery.json")
			client := standDelivery(test, deliveryPath)
			path := filepath.Join(root, slot+"-live", "gateway.json")
			server, err := os.ReadFile(path)
			if err != nil {
				test.Fatal(err)
			}
			fixture := newLeaseMuxRuntime(test, true, client, server, func(_ *leaseMuxFixture, _ *familysession.Session, config *tcpforward.MuxConfig) {
				config.DNSUpstream = dns
				config.Policy.Services = map[string]netip.AddrPort{"chat-api.family-connect.invalid": netip.MustParseAddrPort(origin.Listener.Addr().String())}
			}, 10*time.Second, path, 22*time.Minute)
			closeObserver, err := ObservePublication(fixture.ctx, filepath.Join(root, slot+".sock"), path)
			if err != nil {
				test.Fatal(err)
			}
			defer closeObserver()
			stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			defer stream.Reset()
			initialClient, initialServer := fixture.client, fixture.server
			initialSecurity := fixture.secured.SecurityDeadline()
			initialLease := fixture.broker.setups[fixture.id].lease.deadline()
			ctx, cancel := context.WithCancel(fixture.ctx)
			defer cancel()
			maintenance := NewSessionMaintenance(ctx, fixture.client, fixture.clientSecured, fixture.id, func() { fixture.client.Close() })
			maintenanceDone := make(chan struct{})
			go func() { defer close(maintenanceDone); maintenance.Run() }()
			defer func() {
				cancel()
				select {
				case <-maintenanceDone:
				case <-time.After(time.Second):
					test.Error("maintenance leaked")
				}
			}()
			standReceipt(test, root, slot+"-started", map[string]any{"security": initialSecurity, "lease": initialLease})
			last := sha256.Sum256(client)
			generation, packets := uint64(0), 0
			var firstSecurity time.Time
			completed := make(chan struct{}, 1)
			pending := false
			for {
				if ctx.Err() != nil {
					test.Fatal("runtime expired", ctx.Err())
				}
				payload := []byte(fmt.Sprintf("isolated-sequence-%d", packets))
				received := make([]byte, len(payload))
				if _, err := stream.Write(payload); err != nil {
					test.Fatal("original TCP write", err)
				}
				if _, err := io.ReadFull(stream, received); err != nil || !bytes.Equal(payload, received) {
					test.Fatal("original TCP read", err)
				}
				packets++
				if fixture.client != initialClient || fixture.server != initialServer || fixture.accepted.Load() != 1 {
					test.Fatal("connection replaced")
				}
				select {
				case <-completed:
					pending = false
					generation++
					for _, session := range []*familysession.Session{fixture.secured, fixture.clientSecured} {
						if err := session.WithAuthorization(ctx, func(auth familysession.Authorization) error {
							if auth.Generation != generation {
								return fmt.Errorf("generation mismatch")
							}
							return nil
						}); err != nil {
							test.Fatal(err)
						}
					}
					if generation == 1 {
						firstSecurity = fixture.secured.SecurityDeadline()
					}
					standReceipt(test, root, fmt.Sprintf("%s-generation-%d", slot, generation), map[string]any{"generation": generation, "security": fixture.secured.SecurityDeadline(), "at": time.Now().UTC(), "packets": packets})
				default:
				}
				if generation >= 1 && time.Now().After(initialSecurity.Add(time.Second)) {
					standReceipt(test, root, slot+"-crossed", map[string]any{"at": time.Now().UTC(), "packets": packets})
				}
				if generation == 2 && time.Now().After(firstSecurity.Add(time.Second)) {
					break
				}
				if !pending {
					next := standDelivery(test, deliveryPath)
					sum := sha256.Sum256(next)
					if sum != last {
						if !maintenance.Offer(next, func() { completed <- struct{}{} }) {
							test.Fatal("readiness successor rejected")
						}
						last, pending = sum, true
					}
				}
				time.Sleep(100 * time.Millisecond)
			}
			name, _ := dnsmessage.NewName("renewal.test.")
			query, _ := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 47}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
			answer, err := fixture.client.QueryDNS(ctx, query)
			if err != nil || len(answer) != len(query) || answer[2]&0x80 == 0 {
				test.Fatal("DNS", err)
			}
			fixture.data(test, stream, packets)
			fresh, err := fixture.client.OpenTCP(ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			fresh.Write([]byte("new-flow"))
			received := make([]byte, 8)
			if _, err := io.ReadFull(fresh, received); err != nil || string(received) != "new-flow" {
				test.Fatal("new TCP", err)
			}
			fresh.Reset()
			https, err := fixture.client.OpenTCP(ctx, tcpforward.OpenRequest{Host: "chat-api.family-connect.invalid", Port: 1})
			if err != nil {
				test.Fatal(err)
			}
			roots := x509.NewCertPool()
			roots.AddCert(origin.Certificate())
			secure := tls.Client(integrationTLS{https}, &tls.Config{RootCAs: roots, ServerName: "example.com", MinVersion: tls.VersionTLS13})
			if err := secure.HandshakeContext(ctx); err != nil {
				test.Fatal("verified HTTPS", err)
			}
			io.WriteString(secure, "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
			body, err := io.ReadAll(secure)
			https.Reset()
			if err != nil || !bytes.Contains(body, []byte("verified-isolated-origin")) {
				test.Fatal("verified HTTPS", err)
			}
			standReceipt(test, root, slot+"-finished", map[string]any{"generation": generation, "packets": packets, "at": time.Now().UTC(), "lease": fixture.broker.setups[fixture.id].lease.deadline(), "original_security": initialSecurity, "first_security": firstSecurity, "accepted_tcp": fixture.accepted.Load()})
		})
	}
}
