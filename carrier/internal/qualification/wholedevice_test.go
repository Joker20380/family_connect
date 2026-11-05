package qualification

import (
	"context"
	"encoding/json"
	"io"
	"net"
	"net/netip"
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/gatewayruntime"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func TestProtectedWholeDeviceUsesSharedRuntime(test *testing.T) {
	fixtures := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if fixtures == "" {
		test.Skip("requires disposable ProductStore-issued profiles")
	}
	profile, err := os.ReadFile(filepath.Join(fixtures, "valid.json"))
	if err != nil {
		test.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	relayDone := make(chan error, 1)
	go func() { relayDone <- Relay(ctx, listener) }()
	defer func() { cancel(); <-relayDone }()
	provider := Provider{Address: listener.Addr().String()}
	origin, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	defer origin.Close()
	echoDone := make(chan error, 1)
	go func() {
		connection, err := origin.Accept()
		if err == nil {
			defer connection.Close()
			_, err = io.Copy(connection, connection)
		}
		echoDone <- err
	}()
	defer func() { origin.Close(); <-echoDone }()
	directory := filepath.Join(test.TempDir(), "directory.json")
	gateway := filepath.Join(fixtures, "gateway.json")
	starter := roombroker.PacketGateway{TelemostGateway: roombroker.TelemostGateway{
		CredentialsPath: gateway, Services: map[string]netip.AddrPort{"chat-mailbox.family-connect.invalid": origin.Addr().(*net.TCPAddr).AddrPort()}}, Connect: provider.Gateway}
	gatewayDone := make(chan error, 1)
	go func() {
		gatewayDone <- gatewayruntime.Run(ctx, gatewayruntime.Config{Profile: gateway, Listen: "127.0.0.1:0", Directory: directory, Duration: time.Minute}, provider, provider.Seed, starter)
	}()
	defer func() {
		cancel()
		if err := <-gatewayDone; err != nil {
			test.Error(err)
		}
	}()
	var seed []byte
	for {
		seed, err = os.ReadFile(directory)
		if err == nil {
			break
		}
		if ctx.Err() != nil {
			test.Fatal("SeedManager did not publish")
		}
		time.Sleep(time.Millisecond)
	}
	var protected atomic.Int32
	network, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { protected.Add(1); return true })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	client := Provider{Address: provider.Address, DialContext: network.DialContext}
	transport := wholedevice.PacketTransport{Seed: client.Seed, Dedicated: client.Gateway}
	if session, err := wholedevice.OpenProvisionedWithTransport(ctx, profile, seed, network, func(string) {}, wholedevice.PacketTransport{}); err == nil || session != nil || protected.Load() != 0 {
		test.Fatal("incomplete transport did not fail closed")
	}
	session, err := wholedevice.OpenProvisionedWithTransport(ctx, profile, seed, network, func(string) {}, transport)
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	if protected.Load() < 2 {
		test.Fatal("seed or dedicated transport bypassed protection")
	}
	stream, err := session.OpenService(ctx, "chat-mailbox")
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	if _, err := stream.Write([]byte("shared-wholedevice")); err != nil {
		test.Fatal(err)
	}
	response := make([]byte, len("shared-wholedevice"))
	if _, err := io.ReadFull(stream, response); err != nil || string(response) != "shared-wholedevice" {
		test.Fatal("actual Family mux traffic failed", err)
	}
	if _, err := json.Marshal(session.Snapshot()); err != nil || session.Failed() {
		test.Fatal("shared session diagnostics unavailable")
	}
	session.Close()
	if !session.Failed() {
		test.Fatal("session owner cleanup did not finish")
	}
	denied, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { return false })
	if err != nil {
		test.Fatal(err)
	}
	defer denied.Close()
	client.DialContext = denied.DialContext
	transport = wholedevice.PacketTransport{Seed: client.Seed, Dedicated: client.Gateway}
	bounded, finish := context.WithTimeout(ctx, 100*time.Millisecond)
	defer finish()
	if session, err := wholedevice.OpenProvisionedWithTransport(bounded, profile, seed, denied, func(string) {}, transport); err == nil || session != nil || denied.Rejected.Load() == 0 {
		test.Fatal("failed protection used direct transport")
	}
}
