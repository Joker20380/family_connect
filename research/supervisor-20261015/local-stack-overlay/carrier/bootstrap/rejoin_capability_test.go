//go:build sameroomfixture && seedacceptance

package bootstrap

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/netip"
	"os"
	"path/filepath"
	"runtime"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/internal/rejoinfixture"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

func joinLocal(test *testing.T, ctx context.Context, room, label string) *telemost.Session {
	test.Helper()
	session, err := telemost.New(ctx, telemost.Config{RoomURL: room, DisplayName: label, Mode: telemost.ModeVP8, MaxVideoTracks: 4})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { session.Close() })
	if err = session.Connect(ctx); err != nil {
		test.Fatalf("join boundary: %T %v", err, err)
	}
	return session
}

func TestAcceptanceRealPionContinuity(test *testing.T) { acceptanceRealPion(test, false) }
func TestAcceptanceRealPionReceiptFailure(test *testing.T) {
	if os.Geteuid() == 0 {
		test.Skip("permission fault requires non-root fixture")
	}
	acceptanceRealPion(test, true)
}
func acceptanceRealPion(test *testing.T, receiptFailure bool) {
	goroutinesBefore := runtime.NumGoroutine()
	fdsBefore, _ := os.ReadDir("/proc/self/fd")
	provider := rejoinfixture.Start(test)
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	var err error
	controlDir := test.TempDir()
	os.Chmod(controlDir, 0700)
	if os.Geteuid() == 0 {
		controlDir, err = os.MkdirTemp("/run", "fc-seed-acceptance-media-")
		if err != nil {
			test.Fatal(err)
		}
		defer os.RemoveAll(controlDir)
	}
	binding, err := acceptanceProcessBinding()
	if err != nil {
		test.Fatal(err)
	}
	policy := SeedAcceptanceConfig{Schema: 1, Enabled: true, BinarySHA256: binding.BinarySHA256, Directory: controlDir, ExpiresAt: time.Now().Add(time.Minute)}
	var stopControl func()
	if os.Geteuid() == 0 {
		policyRaw, _ := json.Marshal(policy)
		policyPath := filepath.Join(controlDir, "policy.json")
		if os.WriteFile(policyPath, policyRaw, 0600) != nil {
			test.Fatal("root policy fixture")
		}
		ctx, stopControl, err = StartSeedAcceptance(ctx, policyPath)
	} else {
		ctx, stopControl, err = startSeedAcceptance(ctx, policy, binding, uint32(os.Geteuid()))
	}
	if err != nil {
		test.Fatal(err)
	}
	defer stopControl()
	control := ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
	path := gatewayProfile(test)
	raw := fixture(test, "valid")
	defer clear(raw)
	secondRaw := fixture(test, "valid2")
	defer clear(secondRaw)
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("fixture schema")
	}
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	defer listener.Close()
	var sockets atomic.Int64
	go func() {
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			sockets.Add(1)
			go func() { defer connection.Close(); io.Copy(connection, connection) }()
		}
	}()
	destination := netip.MustParseAddrPort(listener.Addr().String())
	broker, err := roombroker.New(provider, roombroker.TelemostGateway{CredentialsPath: path, Services: map[string]netip.AddrPort{"chat-api.family-connect.invalid": destination}, Event: func(event string) { test.Log("GATEWAY_EVENT", event) }}, roombroker.DefaultLimits(), func(state roombroker.State, code roombroker.Code) { test.Log("BROKER_EVENT", state, code) })
	if err != nil {
		test.Fatal(err)
	}
	defer broker.Close()
	clock := broker.InstallRejoinFixtureClock()
	exchange := func(ctx context.Context, endpoint familysession.PacketEndpoint) {
		OpenServer(ctx, endpoint, path, broker, func(event string) { test.Log("BOOTSTRAP_EVENT", event) })
	}
	published := make(chan Directory, 1)
	endpoints := make(chan *observedSeed, 4)
	seedRooms := make(chan roombroker.Room, 4)
	failures := make(chan SeedFailure, 1)
	recoveries := make(chan SeedRecovery, 32)
	manager := &SeedManager{RecoveryCheck: func(context.Context) (time.Time, error) { return time.Now().Add(time.Hour), nil }, Recovery: func(event SeedRecovery) { recoveries <- event }, Publish: func(directory Directory) error { published <- directory; return nil }, Observe: func(failure SeedFailure) {
		select {
		case failures <- failure:
		default:
		}
	}}
	seedCtx, seedCancel := context.WithCancel(ctx)
	defer seedCancel()
	initialDone := make(chan error, 1)
	go func() {
		initialDone <- manager.Run(seedCtx, provider, func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
			endpoint, err := TelemostSeed(lifetime, ready, room)
			if err == nil {
				seedRooms <- room
				endpoints <- endpoint.(*observedSeed)
			}
			return endpoint, err
		}, credentials.Family, credentials.Gateway, 20*time.Minute, exchange)
	}()
	var directory Directory
	select {
	case directory = <-published:
	case <-ctx.Done():
		test.Fatal("seed initial ready timeout")
	}
	initial := <-endpoints
	roomHash := initial.PacketEndpoint.(*telemost.Session).RejoinFixtureRoomHash()
	seedRoom := <-seedRooms
	serialized, err := json.Marshal(directory)
	if err != nil {
		test.Fatal(err)
	}
	cachePath := filepath.Join(test.TempDir(), "committed-directory.json")
	if os.WriteFile(cachePath, serialized, 0600) != nil {
		test.Fatal("cache fixture write")
	}
	beforeHash := sha256.Sum256(serialized)
	bootstrapCached := func(profile []byte) roombroker.Descriptor {
		test.Helper()
		cached, err := os.ReadFile(cachePath)
		if err != nil {
			test.Fatal(err)
		}
		parsed, err := ParseDirectory(cached, credentials.Family, credentials.Gateway, time.Now())
		if err != nil {
			test.Fatal(err)
		}
		descriptor, err := Recover(ctx, parsed, profile, func(string) {})
		if err != nil {
			test.Fatal("cached bootstrap", err)
		}
		return descriptor
	}
	joinDedicated := func(descriptor roombroker.Descriptor, profile []byte) (*telemost.Session, *tcpforward.Mux) {
		test.Helper()
		carrier := joinLocal(test, ctx, descriptor.JoinURL, "local dedicated client")
		secured, err := familysession.Open(ctx, carrier, profile, false)
		if err != nil {
			test.Fatal("dedicated TLS", err)
		}
		test.Cleanup(func() { secured.Close() })
		if err := roombroker.BindClient(ctx, secured, descriptor, profile); err != nil {
			test.Fatal("dedicated binding", err)
		}
		mux, err := tcpforward.NewMux(ctx, secured, false, tcpforward.MuxConfig{MaxStreams: 32})
		if err != nil {
			test.Fatal(err)
		}
		test.Cleanup(func() { mux.Close() })
		return carrier, mux
	}
	descriptor := bootstrapCached(raw)
	dedicated, mux := joinDedicated(descriptor, raw)
	stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: "chat-api.family-connect.invalid", Port: 1})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	streamID := stream.Stats().ID
	known, err := roombroker.RejoinFixtureLease(ctx, mux, descriptor.SetupID, roombroker.LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	initialLease := known
	var frames atomic.Int64
	trafficDone := make(chan error, 1)
	trafficStop := make(chan struct{})
	go func() {
		for sequence := 0; ; sequence++ {
			select {
			case <-trafficStop:
				trafficDone <- nil
				return
			case <-ctx.Done():
				trafficDone <- ctx.Err()
				return
			default:
			}
			payload := []byte(fmt.Sprintf("same-stream-frame-%08d", sequence))
			if _, err := stream.Write(payload); err != nil {
				trafficDone <- err
				return
			}
			received := make([]byte, len(payload))
			if _, err := io.ReadFull(stream, received); err != nil {
				trafficDone <- err
				return
			}
			if !bytes.Equal(payload, received) {
				trafficDone <- fmt.Errorf("frame mismatch")
				return
			}
			frames.Add(1)
			time.Sleep(20 * time.Millisecond)
		}
	}()
	waitFrames := func(start int64) {
		test.Helper()
		until := time.Now().Add(5 * time.Second)
		for frames.Load() <= start && time.Now().Before(until) {
			time.Sleep(10 * time.Millisecond)
		}
		if frames.Load() <= start {
			test.Fatal("dedicated stream stalled")
		}
	}
	waitFrames(0)
	createdBefore := provider.Snapshot()["room_creates"].(int64)
	if createdBefore != 2 {
		test.Fatal("initial room count", createdBefore)
	}
	oldID := provider.SeedIDForAcceptance()
	binding.Generation = 1
	binding.RoomHash = initial.PacketEndpoint.(*telemost.Session).ResearchRoomHash()
	command := SeedAcceptanceCommand{Schema: 1, Command: acceptanceCommand, Binding: binding, Nonce: fmt.Sprintf("%064x", time.Now().UnixNano()), ArmedAt: time.Now(), ExpiresAt: time.Now().Add(15 * time.Second)}
	invalid := command
	invalid.Binding.Generation++
	invalidRaw, _ := json.Marshal(invalid)
	invalidConnection, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: control.listener.Addr().String(), Net: "unix"})
	if err != nil {
		test.Fatal(err)
	}
	invalidConnection.SetDeadline(time.Now().Add(3 * time.Second))
	invalidConnection.Write(invalidRaw)
	invalidConnection.CloseWrite()
	rejection, _ := io.ReadAll(invalidConnection)
	invalidConnection.Close()
	if string(rejection) != "REJECTED\n" || initial.PacketEndpoint.(*telemost.Session).SignalingReadFailure().Kind != "" {
		test.Fatal("invalid command affected real seed")
	}
	if receiptFailure {
		if os.Chmod(controlDir, 0500) != nil {
			test.Fatal("receipt failure injection")
		}
		defer os.Chmod(controlDir, 0700)
	}
	request, _ := json.Marshal(command)
	connection, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: control.listener.Addr().String(), Net: "unix"})
	if err != nil {
		test.Fatal(err)
	}
	connection.SetDeadline(time.Now().Add(3 * time.Second))
	connection.Write(request)
	connection.CloseWrite()
	response, _ := io.ReadAll(connection)
	connection.Close()
	if string(response) != "CONSUMED\n" {
		test.Fatal("control rejected")
	}

	var active *observedSeed
	concurrentResults := make(chan error, 2)
	for generation := 2; generation <= 3; generation++ {
		firstObserved := false
		for {
			var event SeedRecovery
			select {
			case event = <-recoveries:
			case err := <-initialDone:
				test.Fatal("supervisor exited", err)
			case <-ctx.Done():
				test.Fatal("recovery timeout")
			}
			if event.Outcome == "FIRST_CLOSE" {
				firstObserved = true
				if event.FirstStage != "SEED_READ" || event.FirstSource != "SIGNAL_READ" || event.FirstSignaling.CloseCode != 1011 || event.FirstSignaling.ContextState != "ACTIVE" || event.FirstSignaling.CarrierClosed {
					test.Fatal("classifier", event)
				}
			}
			if event.Outcome == "BACKOFF" && generation == 2 {
				for index := 0; index < 2; index++ {
					go func() {
						bounded, stop := context.WithTimeout(ctx, 700*time.Millisecond)
						defer stop()
						_, err := Recover(bounded, directory, secondRaw, func(string) {})
						concurrentResults <- err
					}()
				}
				clock.Advance(8 * time.Minute)
				known, err = roombroker.RejoinFixtureLease(ctx, mux, descriptor.SetupID, known, true)
				if err != nil || known.Sequence != 1 || known.SetupID != initialLease.SetupID {
					test.Fatal("lease during seed recovery", err)
				}
				waitFrames(frames.Load())
			}
			if event.State == "SEED_ACTIVE" {
				if !firstObserved || event.NewGeneration != uint64(generation) {
					test.Fatal("generation", event)
				}
				encoded, _ := json.Marshal(event)
				test.Log("RECOVERY_RECEIPT", string(encoded))
				break
			}
		}
		active = <-endpoints
		if generation == 2 {
			for index := 0; index < 2; index++ {
				if <-concurrentResults == nil {
					test.Fatal("bootstrap accepted in unavailable window")
				}
			}
			test.Log("CONCURRENT_BOOTSTRAP unavailable_window=2 bounded_rejections=2")
		}
		if active.PacketEndpoint.(*telemost.Session).RejoinFixtureRoomHash() != roomHash {
			test.Fatal("same-room violation")
		}
		if nextRoom := <-seedRooms; nextRoom != seedRoom {
			test.Fatal("new room")
		}
		if provider.WaitRetired(ctx, oldID) != nil {
			test.Fatal("retirement")
		}
		initial.PacketEndpoint.(*telemost.Session).RejoinFixtureOldCallbacks()
		initial.Close()
		if provider.Snapshot()["room_creates"].(int64) != createdBefore {
			test.Fatal("rejoin created room")
		}
		waitFrames(frames.Load())
		manager.mu.Lock()
		currentDirectory := *manager.directory
		manager.mu.Unlock()
		currentBytes, _ := json.Marshal(currentDirectory)
		if !bytes.Equal(serialized, currentBytes) || len(published) != 0 {
			test.Fatal("directory republished or changed")
		}
		if len(failures) != 0 {
			test.Fatal("recovered failure escalated to fatal")
		}
		if generation == 2 {
			oldID, err = provider.CloseSeed(1011)
			if err != nil {
				test.Fatal(err)
			}
			initial = active
		}
	}
	oldCallbacksDone := make(chan struct{})
	time.AfterFunc(10*time.Millisecond, func() {
		initial.PacketEndpoint.(*telemost.Session).RejoinFixtureOldCallbacks()
		close(oldCallbacksDone)
	})
	stopControl()
	if _, err := os.Lstat(filepath.Join(controlDir, "seed-acceptance.sock")); !receiptFailure && !os.IsNotExist(err) {
		test.Fatal("control not cleaned")
	}
	if control.consume(command, time.Now()) {
		test.Fatal("replay after cleanup")
	}
	entries, _ := os.ReadDir(controlDir)
	readerSeen, recovered := false, false
	for _, entry := range entries {
		if entry.Name() == "policy.json" {
			continue
		}
		raw, _ := os.ReadFile(filepath.Join(controlDir, entry.Name()))
		var receipt SeedAcceptanceReceipt
		if json.Unmarshal(raw, &receipt) == nil {
			readerSeen = readerSeen || receipt.ReaderObserved1011
			recovered = recovered || receipt.RecoveryOutcome == "RECOVERED"
			encoded, _ := json.Marshal(receipt)
			test.Log("TRIGGER_RECEIPT", string(encoded))
		}
	}
	if !receiptFailure && (!readerSeen || !recovered) {
		test.Fatal("missing independent trigger reader/recovery receipt")
	}
	if receiptFailure {
		if readerSeen || recovered {
			test.Fatal("receipt write failure not exercised")
		}
		os.Chmod(controlDir, 0700)
		os.Remove(filepath.Join(controlDir, "seed-acceptance.sock"))
		test.Log("RECEIPT_FAILURE_PROTOCOL_CONTINUES true")
	}
	postDescriptor := bootstrapCached(secondRaw)
	<-oldCallbacksDone
	postCarrier, postMux := joinDedicated(postDescriptor, secondRaw)
	if postDescriptor.SetupID == descriptor.SetupID {
		test.Fatal("new client reused holder")
	}
	if provider.Snapshot()["room_creates"].(int64) != createdBefore+1 {
		test.Fatal("unexpected rooms after new dedicated")
	}
	revoked := fixture(test, "revoked")
	rejectedCtx, rejectedCancel := context.WithTimeout(ctx, 5*time.Second)
	_, rejectedErr := Recover(rejectedCtx, directory, revoked, func(string) {})
	rejectedCancel()
	clear(revoked)
	if rejectedErr == nil || provider.Snapshot()["room_creates"].(int64) != createdBefore+1 {
		test.Fatal("revoked bootstrap accepted or allocated room")
	}
	clock.Advance(2*time.Minute + time.Second)
	if !clock.Now().After(initialLease.ExpiresAt) {
		test.Fatal("clock did not cross old lease")
	}
	waitFrames(frames.Load())
	if stream.Stats().ID != streamID || sockets.Load() != 1 {
		test.Fatal("stream/socket replaced")
	}
	after, err := os.ReadFile(cachePath)
	if err != nil || !bytes.Equal(after, serialized) || sha256.Sum256(after) != beforeHash {
		test.Fatal("directory cache changed")
	}
	if _, err := ParseDirectory(after, credentials.Family, credentials.Gateway, directory.ExpiresAt); err == nil {
		test.Fatal("expired directory accepted")
	}
	close(trafficStop)
	if err := <-trafficDone; err != nil {
		test.Fatal("persistent traffic", err)
	}
	stats := active.PacketEndpoint.(*telemost.Session).Stats()
	if initial.SeedSignalingReadFailure().CloseCode != 1011 {
		test.Fatal("cleanup replaced first cause")
	}
	if stats.PublisherState != "connected" || stats.SubscriberState != "connected" || stats.BytesSent == 0 || stats.BytesReceived == 0 {
		test.Fatal("recovered media evidence incomplete")
	}
	receipt := map[string]any{"directory_sha256": fmt.Sprintf("%x", beforeHash), "directory_bytes_unchanged": true, "seed_creates": 1, "total_rooms": provider.Snapshot()["room_creates"], "seed_generations": 3, "same_dedicated_tag": true, "same_mux_stream": true, "tcp_accepts": sockets.Load(), "numbered_frames": frames.Load(), "cached_authenticated_bootstrap_after_rejoin": true, "dedicated_ready_after_rejoin": true, "lease_sequence": known.Sequence, "lease_clock": "CONTROLLED_ONLY_LEASE_CLOCK", "post_old_deadline_frame": true, "recovered_seed_stats": stats, "dedicated_stats": dedicated.Stats(), "provider": provider.Snapshot()}
	encoded, _ := json.Marshal(receipt)
	test.Log("SAME_ROOM_RECEIPT", string(encoded))
	postMux.Close()
	postCarrier.Close()
	mux.Close()
	dedicated.Close()
	seedCancel()
	active.Close()
	<-initialDone
	broker.Close()
	provider.Close()
	listener.Close()
	until := time.Now().Add(3 * time.Second)
	for runtime.NumGoroutine() > goroutinesBefore+8 && time.Now().Before(until) {
		runtime.GC()
		time.Sleep(20 * time.Millisecond)
	}
	fdsAfter, _ := os.ReadDir("/proc/self/fd")
	resource := provider.Snapshot()
	if resource["peak_seed_owners"].(int64) != 1 {
		test.Fatal("parallel seed owner")
	}
	if resource["active_websockets"].(int64) != 0 || resource["peer_connections"].(int64) != 0 || resource["retained_peers"].(int) != 0 || len(fdsAfter) > len(fdsBefore)+2 || runtime.NumGoroutine() > goroutinesBefore+8 {
		test.Fatal("resource leak", len(fdsBefore), len(fdsAfter), goroutinesBefore, runtime.NumGoroutine(), resource["active_websockets"], resource["peer_connections"])
	}
	test.Logf("RESOURCE_FINAL websocket=0 peerconnection=0 peers=0 fd_before=%d fd_after=%d goroutine_before=%d goroutine_after=%d", len(fdsBefore), len(fdsAfter), goroutinesBefore, runtime.NumGoroutine())
}

func TestLocalSFUMedia(test *testing.T) {
	provider := rejoinfixture.Start(test)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	room, err := provider.CreateRoom(ctx)
	if err != nil {
		test.Fatal(err)
	}
	first := joinLocal(test, ctx, room.JoinURL, "Family bootstrap gateway")
	second := joinLocal(test, ctx, room.JoinURL, "local client")
	payload := []byte("synthetic same-room VP8 probe")
	if err := first.SendContext(ctx, payload); err != nil {
		test.Fatal(err)
	}
	got, err := second.Recv(ctx)
	if err != nil || !bytes.Equal(payload, got) {
		test.Fatalf("RTP delivery: %v", err)
	}
	if err := second.SendContext(ctx, payload); err != nil {
		test.Fatal(err)
	}
	got, err = first.Recv(ctx)
	if err != nil || !bytes.Equal(payload, got) {
		test.Fatalf("reverse RTP delivery: %v", err)
	}
	first.Close()
	second.Close()
	receipt, _ := json.Marshal(provider.Snapshot())
	test.Log("LOCAL_SFU", string(receipt))
}
