package roombroker

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"golang.org/x/net/dns/dnsmessage"
)

type integrationTLS struct{ *tcpforward.MuxStream }

func (integrationTLS) LocalAddr() net.Addr              { return &net.TCPAddr{} }
func (integrationTLS) RemoteAddr() net.Addr             { return &net.TCPAddr{} }
func (integrationTLS) SetDeadline(time.Time) error      { return nil }
func (integrationTLS) SetReadDeadline(time.Time) error  { return nil }
func (integrationTLS) SetWriteDeadline(time.Time) error { return nil }

func TestRenewalRuntimeContinuity(test *testing.T) {
	for _, bound := range []string{"leaf", "crl"} {
		test.Run(bound, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			original := time.Now().Add(12 * time.Second).UTC().Truncate(time.Second)
			profiles.limit(test, original.Add(3*time.Second), bound != "leaf")
			profiles.limit(test, original, bound == "leaf")
			origin := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) { io.WriteString(writer, "verified-renewal-origin") }))
			defer origin.Close()
			fixture := newLeaseMuxOptions(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server), func(_ *leaseMuxFixture, _ *familysession.Session, config *tcpforward.MuxConfig) {
				config.Policy.Services = map[string]netip.AddrPort{"chat-api.family-connect.invalid": netip.MustParseAddrPort(origin.Listener.Addr().String())}
				if os.Getenv("FC_RENEWAL_ISOLATED_DNS") == "1" {
					config.DNSUpstream = renewalDNS(test)
				}
			}, 10*time.Second)
			current := fixture.broker.setups[fixture.id]
			oldLease := current.lease.deadline()
			initialClient, initialServer := fixture.client, fixture.server
			stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			defer stream.Reset()
			finished := make(chan struct{})
			ctx, cancel := context.WithCancel(fixture.ctx)
			defer cancel()
			maintenance := NewSessionMaintenance(ctx, fixture.client, fixture.clientSecured, fixture.id, func() { fixture.client.Close() })
			go func() {
				defer close(finished)
				maintenance.Run()
			}()
			defer func() {
				cancel()
				select {
				case <-finished:
				case <-time.After(time.Second):
					test.Error("maintenance leaked")
				}
			}()
			var packets atomic.Int64
			traffic := make(chan error, 1)
			go func() {
				for ctx.Err() == nil {
					payload := []byte(fmt.Sprintf("persistent-%d", packets.Load()))
					received := make([]byte, len(payload))
					if _, err := stream.Write(payload); err != nil {
						traffic <- err
						return
					}
					if _, err := io.ReadFull(stream, received); err != nil {
						traffic <- err
						return
					}
					if !bytes.Equal(payload, received) {
						traffic <- fmt.Errorf("payload changed")
						return
					}
					packets.Add(1)
					select {
					case <-ctx.Done():
						traffic <- nil
						return
					case <-time.After(20 * time.Millisecond):
					}
				}
				traffic <- nil
			}()
			renew := func(generation int64, deadline time.Time) {
				clientNext, serverNext := profiles.successorUntil(test, false, deadline, generation+1, 2+2*generation, 3+2*generation)
				replaceRotationProfile(test, fixture.path, serverNext)
				result := make(chan struct{})
				if !maintenance.Offer(rotationRaw(test, clientNext), func() { close(result) }) {
					test.Fatal("candidate not queued")
				}
				select {
				case <-result:
				case <-fixture.ctx.Done():
					test.Fatal("renewal stalled")
				}
				for _, session := range []*familysession.Session{fixture.secured, fixture.clientSecured} {
					err := session.WithAuthorization(ctx, func(snapshot familysession.Authorization) error {
						if snapshot.Generation != uint64(generation) || !snapshot.Deadline.Equal(deadline) {
							return fmt.Errorf("mixed authorization")
						}
						return nil
					})
					if err != nil {
						test.Fatal(err)
					}
				}
				test.Logf("generation=%d committed_at=%s old_security=%s new_security=%s old_lease=%s", generation, time.Now().UTC().Format(time.RFC3339Nano), original.Format(time.RFC3339Nano), deadline.Format(time.RFC3339Nano), oldLease.Format(time.RFC3339Nano))
			}
			renew(1, original.Add(12*time.Second))
			time.Sleep(time.Until(original) + 150*time.Millisecond)
			if _, err := current.authorize(ctx); err == nil && bound == "leaf" {
				test.Fatal("original control capture unexpectedly valid")
			}
			if current.ctx.Err() != nil || !current.lease.deadline().After(oldLease) {
				test.Fatal("full lease/monitor did not survive old bounds")
			}
			renew(2, original.Add(24*time.Second))
			beforeCrossing := packets.Load()
			time.Sleep(time.Until(original.Add(12*time.Second)) + 150*time.Millisecond)
			if current.ctx.Err() != nil || !current.lease.deadline().After(original.Add(12*time.Second)) {
				test.Fatal("second lease generation did not survive")
			}
			if _, err := current.authorize(ctx); err == nil {
				test.Fatal("expired original control certificate accepted")
			}
			if fixture.client != initialClient || fixture.server != initialServer || fixture.accepted.Load() != 1 || packets.Load() <= beforeCrossing || packets.Load() < 10 {
				test.Fatal("session/socket or continuous traffic lost", fixture.accepted.Load(), beforeCrossing, packets.Load())
			}
			test.Logf("crossed_at=%s packets=%d lease=%s tls_peer_serial=%s auth_peer_serial=%s", time.Now().UTC().Format(time.RFC3339Nano), packets.Load(), current.lease.deadline().Format(time.RFC3339Nano), fixture.secured.ConnectionState().PeerCertificates[0].SerialNumber, fixture.secured.AuthorizationState().PeerCertificates[0].SerialNumber)
			fresh, err := fixture.client.OpenTCP(ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			fresh.Write([]byte("new-flow"))
			received := make([]byte, 8)
			if _, err := io.ReadFull(fresh, received); err != nil || string(received) != "new-flow" {
				test.Fatal("new TCP failed", err)
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
			if err != nil || !bytes.Contains(body, []byte("verified-renewal-origin")) {
				test.Fatal("HTTPS origin response", err)
			}
			test.Run("DNS", func(test *testing.T) {
				if os.Getenv("FC_RENEWAL_ISOLATED_DNS") != "1" {
					test.Skip("isolated port53 required")
				}
				name, _ := dnsmessage.NewName("renewal.test.")
				query, _ := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 47}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
				answer, err := fixture.client.QueryDNS(ctx, query)
				if err != nil || len(answer) != len(query) || answer[2]&0x80 == 0 {
					test.Fatal("DNS after both deadlines", err)
				}
			})
			cancel()
			select {
			case err := <-traffic:
				if err != nil {
					test.Fatal("persistent traffic", err)
				}
			case <-time.After(time.Second):
				test.Fatal("traffic worker leaked")
			}
		})
	}
}
