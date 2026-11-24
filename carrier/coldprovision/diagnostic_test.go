package coldprovision

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"math/big"
	"net"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

func diagnosticFixture(test *testing.T) ([]byte, []byte, tls.Certificate) {
	test.Helper()
	anchor, root, _ := ed25519.GenerateKey(rand.Reader)
	_, issuer, _ := ed25519.GenerateKey(rand.Reader)
	now := time.Now()
	authority := &x509.Certificate{SerialNumber: big.NewInt(1), NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign}
	authorityDER, err := x509.CreateCertificate(rand.Reader, authority, authority, issuer.Public(), issuer)
	if err != nil {
		test.Fatal(err)
	}
	_, key, _ := ed25519.GenerateKey(rand.Reader)
	leaf := &x509.Certificate{SerialNumber: big.NewInt(2), NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), DNSNames: []string{"gateway.family-connect.test"}, KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}}
	leafDER, err := x509.CreateCertificate(rand.Reader, leaf, authority, key.Public(), issuer)
	if err != nil {
		test.Fatal(err)
	}
	encode := func(value any, domain string, signer ed25519.PrivateKey) Envelope {
		raw, err := json.Marshal(value)
		if err != nil {
			test.Fatal(err)
		}
		return Envelope{base64.StdEncoding.EncodeToString(raw), base64.StdEncoding.EncodeToString(ed25519.Sign(signer, append([]byte(domain), raw...)))}
	}
	trust := delegation{1, 1, strings.Repeat("1", 32), strings.Repeat("2", 32), string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: authorityDER})), 1, now.Add(-time.Minute).Unix(), now.Add(time.Minute).Unix()}
	address := Address{1, Protocol, 1, now.Add(-time.Second).Unix(), now.Add(time.Minute).Unix(), "nl-amsterdam-1", "https://telemost.yandex.ru/j/synthetic-local-test", string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: leafDER}))}
	locator, _ := json.Marshal(Locator{1, encode(trust, "family-connect/restricted-issuer/v1\x00", root), encode(address, Domain, issuer)})
	return locator, anchor, tls.Certificate{Certificate: [][]byte{leafDER}, PrivateKey: key}
}

func TestDiagnosticBeforeCarrierAndOpenCause(test *testing.T) {
	locator, anchor, _ := diagnosticFixture(test)
	for _, scenario := range []string{"locator", "carrier", "protect"} {
		test.Run(scenario, func(test *testing.T) {
			diagnostic := NewDiagnostic(time.Second)
			ctx, cancel := context.WithTimeout(WithDiagnostic(context.Background(), diagnostic), time.Second)
			defer cancel()
			input := locator
			if scenario == "locator" {
				input = []byte(`{}`)
			}
			connector := func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				if scenario == "locator" {
					test.Fatal("carrier reached before verification")
				}
				if scenario == "protect" {
					network, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { diagnostic.Protect(false); return false })
					if err != nil {
						test.Fatal(err)
					}
					defer network.Close()
					_, err = network.Dial("udp4", "127.0.0.1:53")
					return nil, err
				}
				return nil, io.EOF
			}
			_, err := Open(ctx, input, anchor, "nl-amsterdam-1", connector)
			if err == nil {
				test.Fatal("failure accepted")
			}
			want := map[string]string{"locator": "REJECTED", "carrier": "EOF", "protect": "SOCKET_DENIED"}[scenario]
			if got := diagnostic.Snapshot(); got.Reason != want {
				test.Fatalf("snapshot: %+v", got)
			}
			if scenario == "carrier" && !errors.Is(err, io.EOF) {
				test.Fatal("Open erased original cause")
			}
		})
	}
}

type diagnosticEndpoint struct {
	incoming, outgoing chan []byte
	ctx                context.Context
}

func (point *diagnosticEndpoint) SendContext(ctx context.Context, raw []byte) error {
	select {
	case point.outgoing <- bytes.Clone(raw):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-point.ctx.Done():
		return point.ctx.Err()
	}
}
func (point *diagnosticEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case raw := <-point.incoming:
		return raw, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-point.ctx.Done():
		return nil, point.ctx.Err()
	}
}
func (*diagnosticEndpoint) Close() error { return nil }

func TestDiagnosticRealTLSAndResponseEOF(test *testing.T) {
	for _, scenario := range []string{"trust", "eof", "write", "validation"} {
		test.Run(scenario, func(test *testing.T) {
			locator, anchor, identity := diagnosticFixture(test)
			if scenario == "trust" {
				_, _, identity = diagnosticFixture(test)
			}
			diagnostic := NewDiagnostic(3 * time.Second)
			ctx, cancel := context.WithTimeout(WithDiagnostic(context.Background(), diagnostic), 3*time.Second)
			defer cancel()
			forward, reverse := make(chan []byte, 64), make(chan []byte, 64)
			clientPoint, serverPoint := &diagnosticEndpoint{reverse, forward, ctx}, &diagnosticEndpoint{forward, reverse, ctx}
			finished := make(chan struct{})
			go func() {
				defer close(finished)
				bootstrap.ServeCarrier(ctx, serverPoint, func(ctx context.Context, point familysession.PacketEndpoint) {
					connection, err := familysession.ReliableConnection(ctx, point)
					if err != nil {
						return
					}
					defer connection.Close()
					secured := tls.Server(connection, &tls.Config{Certificates: []tls.Certificate{identity}, MinVersion: tls.VersionTLS13, NextProtos: []string{Protocol}})
					if secured.HandshakeContext(ctx) != nil {
						return
					}
					var request Request
					if read(secured, &request) == nil {
						secured.CloseWrite()
						<-ctx.Done()
					}
				})
			}()
			defer func() { cancel(); <-finished }()
			client, err := Open(ctx, locator, anchor, "nl-amsterdam-1", func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				return clientPoint, nil
			})
			if scenario == "trust" {
				if !errors.Is(err, ErrRejected) || diagnostic.Snapshot().Reason != "TLS_TRUST" {
					test.Fatalf("trust: %+v", diagnostic.Snapshot())
				}
				return
			}
			if err != nil {
				test.Fatal("local Open failed", diagnostic.Snapshot())
			}
			defer client.Close()
			if scenario == "write" {
				client.connection.Close()
			}
			body := []byte(`{}`)
			if scenario == "validation" {
				body = []byte(`not-json`)
			}
			_, err = client.Post(Challenge, body, strings.Repeat("1", 32))
			if err == nil {
				test.Fatal("failure accepted")
			}
			want := map[string]string{"write": "REQUEST_WRITE", "eof": "RESPONSE_READ", "validation": "REQUEST_VALIDATE"}[scenario]
			if got := diagnostic.Snapshot(); got.FirstFailure != want {
				test.Fatalf("snapshot: %+v", got)
			}
			if scenario == "eof" && diagnostic.Snapshot().Reason != "EOF" {
				test.Fatalf("not EOF: %+v", diagnostic.Snapshot())
			}
		})
	}
}

func TestDiagnosticConcurrentSnapshotAndRedaction(test *testing.T) {
	diagnostic := NewDiagnostic(time.Second)
	diagnostic.Stage("TELEMOST_CONNECT", false)
	diagnostic.Failure(&telemost.ConnectionFailure{Step: "https://secret/room", Code: "token-secret", Status: 9999})
	var workers sync.WaitGroup
	for index := 0; index < 20; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for count := 0; count < 50; count++ {
				diagnostic.Failure(context.Canceled)
				diagnostic.Protect(true)
				diagnostic.Close(true)
				diagnostic.Snapshot()
			}
		}()
	}
	workers.Wait()
	raw, _ := json.Marshal(diagnostic.Snapshot())
	if bytes.Contains(raw, []byte("secret")) || diagnostic.Snapshot().Reason != "IO" {
		test.Fatal("unfiltered or overwritten diagnostic")
	}
	if reasonCode(&net.DNSError{Err: "secret", Name: "private"}) != "DNS" {
		test.Fatal("DNS type lost")
	}
}
