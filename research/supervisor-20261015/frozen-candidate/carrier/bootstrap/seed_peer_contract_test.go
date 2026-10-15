package bootstrap

import (
	"context"
	"errors"
	"io"
	"net"
	"os"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type failedPeerRead struct {
	familysession.PacketEndpoint
	cause error
}

func (peer failedPeerRead) Recv(context.Context) ([]byte, error) { return nil, peer.cause }

type independentPeer struct{ familysession.PacketEndpoint }

func (peer independentPeer) Close() error { return nil }

func TestSeedPerExchangeFailureKeepsSharedCarrier(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	client, server := pair()
	completed := make(chan *lease, 1)
	finished := make(chan error, 1)
	var providerCalls atomic.Int32
	broker, _ := testBroker(test, &providerCalls, nil, "")
	defer broker.Close()
	if err := broker.CaptureOwnership(64, time.Now().Add(time.Minute)); err != nil {
		test.Fatal(err)
	}
	causes := []error{io.EOF, io.ErrUnexpectedEOF, context.DeadlineExceeded, context.Canceled,
		&net.OpError{Op: "read", Err: os.ErrDeadlineExceeded}, syscall.ECONNRESET}
	var index int
	go func() {
		finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			cause := causes[index]
			index++
			err := Exchange(ctx, failedPeerRead{endpoint, cause}, broker, allow)
			if err != roombroker.Code("bootstrap_protocol_rejected") {
				test.Errorf("unexpected per-exchange result: %T", err)
			}
			completed <- endpoint.(*lease)
		})
	}()
	for completedIndex := range causes {
		if _, err := connectLease(ctx, client); err != nil {
			test.Fatal("next admission unavailable", err)
		}
		select {
		case session := <-completed:
			<-session.finished
		case <-ctx.Done():
			test.Fatal("exchange did not release")
		}
		select {
		case err := <-finished:
			test.Fatalf("peer error killed shared carrier: %T", err)
		default:
		}
		for {
			released := 0
			for _, event := range broker.OwnershipSnapshot().Events {
				if event.Action == "release" {
					released++
				}
			}
			if released == completedIndex+1 {
				break
			}
			select {
			case <-ctx.Done():
				test.Fatal("failed peer holder leaked")
			case <-time.After(time.Millisecond):
			}
		}
	}
	if providerCalls.Load() != 0 {
		test.Fatal("invalid peer created dedicated room")
	}
	cancel()
	<-finished
}

func TestSeedMalformedPacketsThenValidRead(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	client, server := pair()
	completed := make(chan struct{}, 1)
	finished := make(chan error, 1)
	go func() {
		finished <- ServeCarrier(ctx, server, func(context.Context, familysession.PacketEndpoint) { completed <- struct{}{} })
	}()
	malformed := [][]byte{[]byte("FCB1"), make([]byte, envelopeSize+packetLimit+1),
		encodePacket(packet{kind: '?', client: [32]byte{1}}),
		encodePacket(packet{kind: 'O', client: [32]byte{1}, data: []byte{1}})}
	for index := 0; index < 128; index++ {
		if err := client.SendContext(ctx, malformed[index%len(malformed)]); err != nil {
			test.Fatal(err)
		}
	}
	if _, err := connectLease(ctx, client); err != nil {
		test.Fatal(err)
	}
	select {
	case <-completed:
	case <-ctx.Done():
		test.Fatal("valid packet after malformed packets not served")
	}
	cancel()
	if err := <-finished; !errors.Is(err, roombroker.Code("seed_closed")) {
		test.Fatal("shutdown contract changed")
	}
}

func TestSeedAuthRejectThenNextPeer(test *testing.T) {
	path := gatewayProfile(test)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	client, server := pair()
	completed := make(chan *lease, 1)
	finished := make(chan error, 1)
	var providerCalls, authenticated atomic.Int32
	broker, _ := testBroker(test, &providerCalls, nil, "")
	defer broker.Close()
	go func() {
		finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			OpenServer(ctx, endpoint, path, broker, func(event string) {
				if event == "bootstrap_family_auth" {
					authenticated.Add(1)
				}
			})
			completed <- endpoint.(*lease)
		})
	}()
	for _, profile := range []string{"unknown", "valid"} {
		descriptor, err := recoverCarrier(ctx, independentPeer{client}, fixture(test, profile), func(string) {})
		if profile == "unknown" && (err == nil || descriptor.SetupID != "" || providerCalls.Load() != 0 || authenticated.Load() != 0) {
			test.Fatal("auth failure not fail closed")
		}
		if profile == "valid" && (err != nil || descriptor.SetupID == "" || providerCalls.Load() != 1 || authenticated.Load() != 1) {
			test.Fatal("next valid peer rejected", err)
		}
		select {
		case session := <-completed:
			<-session.finished
		case <-ctx.Done():
			test.Fatal("auth exchange did not release")
		}
		select {
		case <-finished:
			test.Fatal("auth peer killed shared carrier")
		default:
		}
	}
	cancel()
	<-finished
}
