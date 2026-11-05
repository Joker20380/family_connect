package roombroker

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/pem"
	"errors"
	"io"
	"net"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"golang.org/x/net/dns/dnsmessage"
)

type renewalTestChannel struct {
	*tcpforward.MuxStream
	transform func([]byte) []byte
}

func (channel renewalTestChannel) Write(raw []byte) (int, error) {
	if channel.transform != nil {
		raw = channel.transform(bytes.Clone(raw))
	}
	return channel.MuxStream.Write(raw)
}

func (profiles *rotationProfiles) limit(test *testing.T, deadline time.Time, leaf bool) {
	test.Helper()
	for _, credentials := range []*familysession.Credentials{&profiles.client, &profiles.server} {
		if !leaf {
			credentials.Revocations = profiles.crl(test, 1, deadline, nil)
			continue
		}
		pair, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
		if err != nil {
			test.Fatal(err)
		}
		template, err := x509.ParseCertificate(pair.Certificate[0])
		if err != nil {
			test.Fatal(err)
		}
		template.NotAfter = deadline
		certificate := rotationCertificate(test, template, profiles.authority, template.PublicKey, profiles.key)
		credentials.Certificate = string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certificate.Raw}))
	}
}

func renewalDNS(test *testing.T) string {
	test.Helper()
	listener, err := net.Listen("tcp4", "127.0.0.1:53")
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { listener.Close() })
	go func() {
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			go func() {
				defer connection.Close()
				connection.SetDeadline(time.Now().Add(5 * time.Second))
				var header [2]byte
				if _, err := io.ReadFull(connection, header[:]); err != nil {
					return
				}
				raw := make([]byte, binary.BigEndian.Uint16(header[:]))
				if len(raw) < 12 || len(raw) > 4096 {
					return
				}
				if _, err := io.ReadFull(connection, raw); err != nil {
					return
				}
				raw[2] |= 0x80
				connection.Write(append(header[:], raw...))
			}()
		}
	}()
	return listener.Addr().String()
}

func renewalExchangeFixture(test *testing.T, profiles *rotationProfiles, serverTransform func([]byte) []byte) (*leaseMuxFixture, <-chan error) {
	test.Helper()
	results := make(chan error, 4)
	dns := ""
	if os.Getenv("FC_RENEWAL_ISOLATED_DNS") == "1" {
		if os.Geteuid() != 0 {
			test.Fatal("DNS qualification requires the isolated root network namespace")
		}
		dns = renewalDNS(test)
	}
	fixture := newLeaseMuxProfileOptions(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server),
		func(fixture *leaseMuxFixture, secured *familysession.Session, config *tcpforward.MuxConfig) {
			config.DNSUpstream = dns
			config.CredentialRenewal = func(ctx context.Context, stream *tcpforward.MuxStream) {
				raw, err := LoadCredentials(fixture.path)
				if err == nil {
					err = secured.RenewCredentials(ctx, renewalTestChannel{stream, serverTransform}, raw)
				}
				clear(raw)
				results <- err
			}
		})
	return fixture, results
}

func exchangeCredentials(test *testing.T, fixture *leaseMuxFixture, credentials familysession.Credentials, ctx context.Context, transform func([]byte) []byte) error {
	test.Helper()
	stream, err := fixture.client.OpenTCP(ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: tcpforward.CredentialRenewalPort})
	if err != nil {
		return err
	}
	return fixture.clientSecured.RenewCredentials(ctx, renewalTestChannel{stream, transform}, rotationRaw(test, credentials))
}

func awaitCredentialResult(test *testing.T, results <-chan error) error {
	test.Helper()
	select {
	case err := <-results:
		return err
	case <-time.After(3 * time.Second):
		test.Fatal("credential exchange did not terminate")
		return nil
	}
}

func TestCredentialExchangeSurvivesOriginalDeadline(test *testing.T) {
	for _, bound := range []string{"leaf", "crl"} {
		test.Run(bound, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			oldDeadline := time.Now().Add(6 * time.Second).UTC().Truncate(time.Second)
			profiles.limit(test, oldDeadline, bound == "leaf")
			fixture, results := renewalExchangeFixture(test, profiles, nil)
			stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			defer stream.Reset()
			fixture.data(test, stream, 0)
			bulk := make(chan error, 1)
			started := make(chan struct{})
			go func() {
				payload := bytes.Repeat([]byte("renewal-with-concurrent-traffic"), 256)
				received := make([]byte, len(payload))
				close(started)
				for index := 0; index < 24; index++ {
					if _, err := stream.Write(payload); err != nil {
						bulk <- err
						return
					}
					if _, err := io.ReadFull(stream, received); err != nil {
						bulk <- err
						return
					}
					if !bytes.Equal(payload, received) {
						bulk <- errors.New("concurrent renewal payload mismatch")
						return
					}
				}
				bulk <- nil
			}()
			<-started
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			if err := exchangeCredentials(test, fixture, clientNext, fixture.ctx, nil); err != nil {
				test.Fatal("client exchange failed", err)
			}
			if err := awaitCredentialResult(test, results); err != nil {
				test.Fatal("server exchange failed", err)
			}
			if err := awaitCredentialResult(test, bulk); err != nil {
				test.Fatal("concurrent traffic failed", err)
			}
			if !fixture.secured.SecurityDeadline().After(oldDeadline) || !fixture.clientSecured.SecurityDeadline().Equal(fixture.secured.SecurityDeadline()) {
				test.Fatal("both peers did not commit the same successor bound")
			}
			if fixture.secured.ConnectionState().PeerCertificates[0].SerialNumber.Int64() != 2 ||
				fixture.secured.AuthorizationState().PeerCertificates[0].SerialNumber.Int64() != 4 {
				test.Fatal("handshake state and renewed authorization were conflated")
			}
			if _, err := SessionAuthorizer(fixture.path, fixture.secured.AuthorizationState())(fixture.ctx); err != nil {
				test.Fatal("successor authorization rejected", err)
			}
			fixture.data(test, stream, 1)
			time.Sleep(time.Until(oldDeadline) + 100*time.Millisecond)
			fixture.data(test, stream, 2)
			test.Run("DNS", func(test *testing.T) {
				if os.Getenv("FC_RENEWAL_ISOLATED_DNS") != "1" {
					test.Skip("requires the isolated port53 DNS harness")
				}
				name, _ := dnsmessage.NewName("renewal.test.")
				query, err := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 78}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
				if err != nil {
					test.Fatal(err)
				}
				response, err := fixture.client.QueryDNS(fixture.ctx, query)
				if err != nil || len(response) != len(query) || response[2]&0x80 == 0 {
					test.Fatal("DNS did not survive the original credential boundary", err)
				}
			})
			if fixture.client.Stats().ProtocolErrors != 0 || fixture.server.Stats().ProtocolErrors != 0 {
				test.Fatal("renewal damaged mux framing")
			}
		})
	}
}

func TestCredentialExchangeUnsafeProfilesNeverExtend(test *testing.T) {
	for _, fault := range []string{"revoked-predecessor", "foreign-authority", "wrong-family", "stale-crl-floor", "wrong-key", "revision", "gateway"} {
		test.Run(fault, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			fixture, results := renewalExchangeFixture(test, profiles, nil)
			before := fixture.secured.SecurityDeadline()
			clientNext, serverNext := profiles.successor(test, fault == "revoked-predecessor")
			switch fault {
			case "foreign-authority":
				clientNext = newRotationProfiles(test, true).client
			case "wrong-family":
				clientNext.Family = strings.Repeat("b", 32)
			case "stale-crl-floor":
				clientNext.MinimumCRL++
			case "wrong-key":
				clientNext.PrivateKey = serverNext.PrivateKey
			case "revision":
				clientNext.MinimumRevision++
			case "gateway":
				clientNext.Gateway = strings.Repeat("b", 32)
			}
			replaceRotationProfile(test, fixture.path, serverNext)
			if err := exchangeCredentials(test, fixture, clientNext, fixture.ctx, nil); err == nil {
				test.Fatal("unsafe successor accepted")
			}
			if err := awaitCredentialResult(test, results); err == nil {
				test.Fatal("peer committed an unacknowledged successor")
			}
			if !fixture.secured.SecurityDeadline().Equal(before) || !fixture.clientSecured.SecurityDeadline().Equal(before) {
				test.Fatal("failed validation extended credentials")
			}
		})
	}
}

func flipRenewalProof(raw []byte) []byte {
	start := bytes.Index(raw, []byte(`"proof":"`))
	if start >= 0 {
		start += len(`"proof":"`)
		if raw[start] == 'A' {
			raw[start] = 'B'
		} else {
			raw[start] = 'A'
		}
	}
	return raw
}

func TestCredentialExchangeCorruptionAndPartialCommitClose(test *testing.T) {
	for _, phase := range []string{"server-proof", "server-committed"} {
		test.Run(phase, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			fixture, results := renewalExchangeFixture(test, profiles, func(raw []byte) []byte {
				if bytes.Contains(raw, []byte(`"kind":"`+phase+`"`)) {
					return flipRenewalProof(raw)
				}
				return raw
			})
			before := fixture.clientSecured.SecurityDeadline()
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			if exchangeCredentials(test, fixture, clientNext, fixture.ctx, nil) == nil || awaitCredentialResult(test, results) == nil {
				test.Fatal("corrupt confirmation accepted")
			}
			if !fixture.clientSecured.SecurityDeadline().Equal(before) {
				test.Fatal("unconfirmed client extended its lifetime")
			}
			for _, session := range []*familysession.Session{fixture.clientSecured, fixture.secured} {
				select {
				case <-session.Done():
				case <-time.After(time.Second):
					test.Fatal("ambiguous commit left a live one-sided session")
				}
			}
		})
	}
}

func TestCredentialExchangeProofCannotCrossSessions(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	clientNext, serverNext := profiles.successor(test, false)
	var proof []byte
	for attempt := 0; attempt < 2; attempt++ {
		fixture, results := renewalExchangeFixture(test, profiles, nil)
		replaceRotationProfile(test, fixture.path, serverNext)
		err := exchangeCredentials(test, fixture, clientNext, fixture.ctx, func(raw []byte) []byte {
			if bytes.Contains(raw, []byte(`"kind":"client-proof"`)) {
				if attempt == 0 {
					proof = bytes.Clone(raw)
				} else {
					return bytes.Clone(proof)
				}
			}
			return raw
		})
		peerError := awaitCredentialResult(test, results)
		if attempt == 0 && (err != nil || peerError != nil || len(proof) == 0) || attempt == 1 && (err == nil || peerError == nil) {
			test.Fatal("session-bound proof replay boundary failed", err, peerError)
		}
	}
}

func TestCredentialExchangeLegacyPeerKeepsTraffic(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture := newLeaseMuxWithProfiles(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server))
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	before := fixture.clientSecured.SecurityDeadline()
	_, err = fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: tcpforward.CredentialRenewalPort})
	var failure *tcpforward.OpenError
	if !errors.As(err, &failure) || failure.Code != "policy_rejected" || !fixture.clientSecured.SecurityDeadline().Equal(before) {
		test.Fatal("unsupported renewal changed the legacy contract", err)
	}
	fixture.data(test, stream, 0)
}

func TestCredentialExchangeCancelBeforeCommit(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture, results := renewalExchangeFixture(test, profiles, nil)
	before := fixture.secured.SecurityDeadline()
	clientNext, serverNext := profiles.successor(test, false)
	replaceRotationProfile(test, fixture.path, serverNext)
	ctx, cancel := context.WithCancel(fixture.ctx)
	defer cancel()
	entered, completed := make(chan struct{}), make(chan error, 1)
	go func() {
		completed <- exchangeCredentials(test, fixture, clientNext, ctx, func(raw []byte) []byte {
			if bytes.Contains(raw, []byte(`"kind":"client-commit"`)) {
				close(entered)
				<-ctx.Done()
			}
			return raw
		})
	}()
	select {
	case <-entered:
	case <-time.After(3 * time.Second):
		test.Fatal("commit barrier not reached")
	}
	cancel()
	if awaitCredentialResult(test, completed) == nil || awaitCredentialResult(test, results) == nil {
		test.Fatal("cancelled commit accepted")
	}
	if !fixture.secured.SecurityDeadline().Equal(before) || !fixture.clientSecured.SecurityDeadline().Equal(before) {
		test.Fatal("cancellation extended the generation")
	}
}

func TestCredentialExchangeRejectsVersionGenerationAndOversize(test *testing.T) {
	for _, fault := range []string{"version", "generation", "oversize", "duplicate-field"} {
		test.Run(fault, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			fixture, results := renewalExchangeFixture(test, profiles, nil)
			before := fixture.secured.SecurityDeadline()
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			err := exchangeCredentials(test, fixture, clientNext, fixture.ctx, func(raw []byte) []byte {
				if !bytes.Contains(raw, []byte(`"kind":"hello"`)) {
					return raw
				}
				switch fault {
				case "version":
					return bytes.Replace(raw, []byte(`"version":1`), []byte(`"version":2`), 1)
				case "generation":
					return bytes.Replace(raw, []byte(`"generation":1`), []byte(`"generation":0`), 1)
				case "oversize":
					binary.BigEndian.PutUint32(raw, 8193)
				case "duplicate-field":
					raw = bytes.Replace(raw, []byte(`"version":1`), []byte(`"version":1,"version":1`), 1)
					binary.BigEndian.PutUint32(raw, uint32(len(raw)-4))
				}
				return raw
			})
			if err == nil || awaitCredentialResult(test, results) == nil {
				test.Fatal("malformed protocol accepted")
			}
			if !fixture.secured.SecurityDeadline().Equal(before) || !fixture.clientSecured.SecurityDeadline().Equal(before) {
				test.Fatal("invalid exchange changed the security deadline")
			}
		})
	}
}

func TestCredentialExchangeLateConfirmationCannotResurrect(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	deadline := time.Now().Add(4 * time.Second).UTC().Truncate(time.Second)
	profiles.limit(test, deadline, true)
	fixture, results := renewalExchangeFixture(test, profiles, func(raw []byte) []byte {
		if bytes.Contains(raw, []byte(`"kind":"server-committed"`)) {
			time.Sleep(time.Until(deadline) + 200*time.Millisecond)
		}
		return raw
	})
	clientNext, serverNext := profiles.successor(test, false)
	replaceRotationProfile(test, fixture.path, serverNext)
	if exchangeCredentials(test, fixture, clientNext, fixture.ctx, nil) == nil || awaitCredentialResult(test, results) == nil {
		test.Fatal("late confirmation revived expired credentials")
	}
	if !fixture.clientSecured.SecurityDeadline().Equal(deadline) {
		test.Fatal("client accepted a proof after its hard bound")
	}
	for _, session := range []*familysession.Session{fixture.clientSecured, fixture.secured} {
		select {
		case <-session.Done():
		case <-time.After(time.Second):
			test.Fatal("late commit did not fence the session")
		}
	}
}

func TestCredentialExchangeRepeatedGeneration(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture, results := renewalExchangeFixture(test, profiles, nil)
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	for generation := int64(1); generation <= 2; generation++ {
		deadline := profiles.now.Add(time.Duration(70+20*generation) * time.Minute)
		clientNext, serverNext := profiles.successorUntil(test, false, deadline, generation+1, 2+2*generation, 3+2*generation)
		replaceRotationProfile(test, fixture.path, serverNext)
		if exchangeCredentials(test, fixture, clientNext, fixture.ctx, nil) != nil || awaitCredentialResult(test, results) != nil {
			test.Fatal("consecutive authenticated generation failed", generation)
		}
		if !fixture.clientSecured.SecurityDeadline().Equal(deadline) || !fixture.secured.SecurityDeadline().Equal(deadline) ||
			fixture.secured.AuthorizationState().PeerCertificates[0].SerialNumber.Int64() != 2+2*generation {
			test.Fatal("successor generation or certificate was not installed")
		}
		fixture.data(test, stream, int(generation))
	}
}
