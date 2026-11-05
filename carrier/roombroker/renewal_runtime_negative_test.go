package roombroker

import (
	"bytes"
	"context"
	"crypto/x509"
	"math/big"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

func runtimeFixture(test *testing.T, profiles *rotationProfiles, lifetime time.Duration) *leaseMuxFixture {
	return newLeaseMuxOptions(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server), nil, lifetime)
}

func runtimeCurrent(fixture *leaseMuxFixture) *setup {
	fixture.broker.mu.Lock()
	defer fixture.broker.unlock()
	return fixture.broker.setups[fixture.id]
}

func runtimeControl(test *testing.T, fixture *leaseMuxFixture, raw []byte) *tcpforward.MuxStream {
	test.Helper()
	candidate, err := fixture.clientSecured.Candidate(raw)
	if err != nil {
		test.Fatal(err)
	}
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: tcpforward.CredentialRenewalPort})
	if err != nil {
		test.Fatal(err)
	}
	if _, err = credentialMessage(stream, &credentialOffer{1, true, candidate}); err != nil {
		test.Fatal(err)
	}
	response, err := credentialMessage(stream, nil)
	if err != nil || !response.Ready {
		test.Fatal("preflight", err)
	}
	return stream
}

func requireRuntimeClosed(test *testing.T, fixture *leaseMuxFixture, current *setup) {
	test.Helper()
	select {
	case <-current.done:
	case <-time.After(2 * time.Second):
		test.Fatal("gateway/broker worker retained")
	}
	for _, session := range []*familysession.Session{fixture.clientSecured, fixture.secured} {
		select {
		case <-session.Done():
		case <-time.After(time.Second):
			test.Fatal("native owner retained")
		}
	}
	if stats := fixture.server.Stats(); stats.ActiveStreams != 0 || stats.ActiveSockets != 0 || stats.RetainedBytes != 0 {
		test.Fatal("gateway resources retained", stats)
	}
}

func TestRenewalRuntimeCandidateOwnership(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture := runtimeFixture(test, profiles, 5*time.Second)
	ctx, cancel := context.WithCancel(fixture.ctx)
	defer cancel()
	owner := NewSessionMaintenance(ctx, fixture.client, fixture.clientSecured, fixture.id, func() { fixture.client.Close() })
	if owner.Offer(rotationRaw(test, profiles.client), nil) {
		test.Fatal("unchanged queued")
	}
	if owner.Offer([]byte("invalid"), nil) {
		test.Fatal("invalid queued")
	}
	clientNext, serverNext := profiles.successor(test, false)
	replaceRotationProfile(test, fixture.path, serverNext)
	raw := rotationRaw(test, clientNext)
	confirmed := make(chan struct{})
	if !owner.Offer(raw, func() { close(confirmed) }) {
		test.Fatal("successor not queued")
	}
	for index := 0; index < 20; index++ {
		if owner.Offer(raw, func() { test.Error("duplicate callback") }) {
			test.Fatal("duplicate queued")
		}
	}
	done := make(chan struct{})
	go func() { defer close(done); owner.Run() }()
	select {
	case <-confirmed:
	case <-time.After(3 * time.Second):
		test.Fatal("candidate not committed")
	}
	if owner.Offer(raw, nil) {
		test.Fatal("confirmed duplicate queued")
	}
	cancel()
	<-done
	if owner.Offer(rotationRaw(test, profiles.client), nil) {
		test.Fatal("closed owner accepted delivery")
	}
	if len(owner.seen) != 1 || len(owner.updates) != 0 {
		test.Fatal("candidate bookkeeping leak")
	}
}

func TestRenewalRuntimeNotReadyAndLegacy(test *testing.T) {
	for _, legacy := range []bool{false, true} {
		test.Run(map[bool]string{true: "legacy", false: "different-crl"}[legacy], func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			var fixture *leaseMuxFixture
			if legacy {
				fixture = newLeaseMuxWithProfiles(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server))
			} else {
				fixture = runtimeFixture(test, profiles, 5*time.Second)
			}
			before := fixture.clientSecured.SecurityDeadline()
			clientNext, _ := profiles.successor(test, false)
			if changed, err := ExchangeCredentials(fixture.ctx, fixture.client, fixture.clientSecured, rotationRaw(test, clientNext)); changed || err != nil {
				test.Fatal("unready successor started exchange", changed, err)
			}
			if !fixture.clientSecured.SecurityDeadline().Equal(before) {
				test.Fatal("unready extended bound")
			}
			stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
			if err != nil {
				test.Fatal(err)
			}
			defer stream.Reset()
			fixture.data(test, stream, 1)
		})
	}
}

func TestRenewalRuntimeDenialBeforeCommit(test *testing.T) {
	for _, fault := range []string{"revoke", "cancel", "disconnect", "lease-expiry"} {
		test.Run(fault, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			lifetime := 5 * time.Second
			if fault == "lease-expiry" {
				lifetime = 1500 * time.Millisecond
			}
			fixture := runtimeFixture(test, profiles, lifetime)
			current := runtimeCurrent(fixture)
			before, lease := fixture.secured.SecurityDeadline(), current.lease.deadline()
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			raw := rotationRaw(test, clientNext)
			stream := runtimeControl(test, fixture, raw)
			held, release := make(chan struct{}), make(chan struct{})
			var once sync.Once
			defer once.Do(func() { close(release) })
			result := make(chan error, 1)
			go func() {
				result <- fixture.clientSecured.RenewCredentials(fixture.ctx, renewalTestChannel{stream, func(raw []byte) []byte {
					if bytes.Contains(raw, []byte(`"kind":"client-commit"`)) {
						close(held)
						<-release
					}
					return raw
				}}, raw)
			}()
			select {
			case <-held:
			case <-time.After(time.Second):
				test.Fatal("commit not held")
			}
			switch fault {
			case "revoke":
				serverNext.Revocations = profiles.crl(test, 3, profiles.now.Add(100*time.Minute), []x509.RevocationListEntry{{SerialNumber: big.NewInt(2), RevocationTime: profiles.now}, {SerialNumber: big.NewInt(4), RevocationTime: profiles.now}})
				serverNext.MinimumCRL = 3
				replaceRotationProfile(test, fixture.path, serverNext)
			case "cancel":
				if fixture.broker.Cancel(fixture.ctx, fixture.id, current.authorize) != nil {
					test.Fatal("cancel failed")
				}
			case "disconnect":
				fixture.client.Close()
			case "lease-expiry":
				time.Sleep(time.Until(lease) + 50*time.Millisecond)
			}
			once.Do(func() { close(release) })
			select {
			case err := <-result:
				if err == nil {
					test.Fatal("late commit revived denied session")
				}
			case <-time.After(2 * time.Second):
				test.Fatal("denied exchange stuck")
			}
			requireRuntimeClosed(test, fixture, current)
			if !fixture.secured.SecurityDeadline().Equal(before) || !current.lease.deadline().Equal(lease) {
				test.Fatal("denied authorization or lease extended")
			}
		})
	}
}

type lostConfirmation struct{ *tcpforward.MuxStream }

func (channel lostConfirmation) Write(raw []byte) (int, error) {
	if bytes.Contains(raw, []byte(`"kind":"client-done"`)) {
		return len(raw), nil
	}
	return channel.MuxStream.Write(raw)
}

func TestRenewalRuntimePartialCommitCloses(test *testing.T) {
	for _, fault := range []string{"corrupt", "lost"} {
		test.Run(fault, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			fixture := runtimeFixture(test, profiles, 5*time.Second)
			current := runtimeCurrent(fixture)
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			raw := rotationRaw(test, clientNext)
			stream := runtimeControl(test, fixture, raw)
			var channel familysession.RenewalChannel = lostConfirmation{stream}
			if fault == "corrupt" {
				channel = renewalTestChannel{stream, func(raw []byte) []byte {
					if bytes.Contains(raw, []byte(`"kind":"client-done"`)) {
						return flipRenewalProof(raw)
					}
					return raw
				}}
			}
			if fixture.clientSecured.RenewCredentials(fixture.ctx, channel, raw) == nil {
				test.Fatal("partial exchange reported success")
			}
			requireRuntimeClosed(test, fixture, current)
		})
	}
}

func TestRenewalRuntimeConcurrentControlDrains(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture := runtimeFixture(test, profiles, 5*time.Second)
	known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	clientNext, serverNext := profiles.successor(test, false)
	replaceRotationProfile(test, fixture.path, serverNext)
	raw := rotationRaw(test, clientNext)
	stream := runtimeControl(test, fixture, raw)
	leaseDone := make(chan error, 1)
	go func() {
		_, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
		leaseDone <- err
	}()
	if err := fixture.clientSecured.RenewCredentials(fixture.ctx, stream, raw); err != nil {
		test.Fatal(err)
	}
	select {
	case err := <-leaseDone:
		if err == tcpforward.ErrStreamLimit {
			_, _, err = exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
		}
		if err != nil {
			test.Fatal("concurrent lease", err)
		}
	case <-time.After(2 * time.Second):
		test.Fatal("control starvation")
	}
	limit := time.Now().Add(time.Second)
	for time.Now().Before(limit) {
		if fixture.client.Stats().ActiveStreams == 0 && fixture.server.Stats().ActiveStreams == 0 {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	test.Fatal("control streams retained", fixture.client.Stats(), fixture.server.Stats())
}
