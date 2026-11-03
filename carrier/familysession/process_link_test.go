package familysession

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"os/exec"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type processLinkConfig struct {
	Profile Credentials
	Remote  string
	Server  bool
	Rate    int
	Window  int
}

type processLinkResult struct {
	Address         string
	Error           string
	Bytes           int
	Retransmissions uint64
	Drops           int
}

func TestFamilyProcessCompatibility(test *testing.T) {
	current, err := os.Executable()
	if err != nil {
		test.Fatal(err)
	}
	test.Run("current-current", func(test *testing.T) { runFamilyProcesses(test, current, current, 0, 8) })
	if baseline := os.Getenv("FC_FAMILY_BASELINE_BINARY"); baseline != "" {
		test.Run("current-baseline", func(test *testing.T) { runFamilyProcesses(test, current, baseline, 0, 8) })
		test.Run("baseline-current", func(test *testing.T) { runFamilyProcesses(test, baseline, current, 0, 8) })
		test.Run("baseline-baseline", func(test *testing.T) { runFamilyProcesses(test, baseline, baseline, 0, 8) })
	}
}

func TestFamilyProcessPacedLink(test *testing.T) {
	if os.Getenv("FC_FAMILY_PACED_LINK") != "1" {
		test.Skip("opt-in wall-clock paced UDP integration, not a provider/handset test")
	}
	current, err := os.Executable()
	if err != nil {
		test.Fatal(err)
	}
	for _, rate := range []int{256, 512, 1000} {
		for _, window := range []int{8, 32} {
			test.Run(fmt.Sprintf("%dkbit-window%d", rate, window), func(test *testing.T) {
				runFamilyProcesses(test, current, current, rate, window)
			})
		}
	}
}

func runFamilyProcesses(test *testing.T, clientBinary, serverBinary string, rate, window int) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	clientProfile, serverProfile := profiles(test)
	var commands [2]*exec.Cmd
	var inputs [2]*json.Encoder
	var outputs [2]*json.Decoder
	var addresses [2]string
	for index, binary := range []string{clientBinary, serverBinary} {
		command := exec.CommandContext(ctx, binary, "-test.run=^TestFamilyProcessHelper$")
		command.Env = append(os.Environ(), "FC_FAMILY_PROCESS_HELPER=1")
		input, err := command.StdinPipe()
		if err != nil {
			test.Fatal(err)
		}
		output, err := command.StdoutPipe()
		if err != nil {
			test.Fatal(err)
		}
		if err := command.Start(); err != nil {
			test.Fatal(err)
		}
		test.Cleanup(func() {
			input.Close()
			output.Close()
			if command.ProcessState == nil {
				command.Process.Kill()
				command.Wait()
			}
		})
		commands[index], inputs[index], outputs[index] = command, json.NewEncoder(input), json.NewDecoder(output)
		var result processLinkResult
		if err := outputs[index].Decode(&result); err != nil || result.Error != "" {
			test.Fatalf("endpoint startup: %v %s", err, result.Error)
		}
		addresses[index] = result.Address
	}
	for index, profile := range []Credentials{clientProfile, serverProfile} {
		directionRate := rate
		if index == 1 {
			directionRate /= 4
		}
		if err := inputs[index].Encode(processLinkConfig{Profile: profile, Remote: addresses[1-index], Server: index == 1, Rate: directionRate, Window: window}); err != nil {
			test.Fatal(err)
		}
	}
	failed := false
	for index := range commands {
		var result processLinkResult
		if err := outputs[index].Decode(&result); err != nil || result.Error != "" || result.Bytes != 8*32768 {
			test.Errorf("endpoint%d transfer: %v %+v", index, err, result)
			failed = true
			continue
		}
		if rate > 0 && (result.Drops == 0 || result.Retransmissions == 0) {
			test.Fatalf("endpoint%d fault was not exercised: %+v", index, result)
		}
		test.Logf("endpoint%d: %d byte-exact bytes, %d initial DATA drops, %d retransmissions", index, result.Bytes, result.Drops, result.Retransmissions)
	}
	if failed {
		return
	}
	for index, command := range commands {
		if err := inputs[index].Encode("close"); err != nil {
			test.Fatal(err)
		}
		if err := command.Wait(); err != nil {
			test.Fatal("endpoint cleanup:", err)
		}
	}
}

func TestFamilyProcessHelper(test *testing.T) {
	if os.Getenv("FC_FAMILY_PROCESS_HELPER") != "1" {
		test.Skip("private subprocess helper")
	}
	if err := familyProcessEndpoint(); err != nil {
		json.NewEncoder(os.Stdout).Encode(processLinkResult{Error: err.Error()})
		os.Exit(1)
	}
	os.Exit(0)
}

func familyProcessEndpoint() (failure error) {
	ctx, cancel := context.WithTimeout(context.Background(), 115*time.Second)
	defer cancel()
	connection, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		return err
	}
	defer connection.Close()
	output, input := json.NewEncoder(os.Stdout), json.NewDecoder(os.Stdin)
	if err := output.Encode(processLinkResult{Address: connection.LocalAddr().String()}); err != nil {
		return err
	}
	var config processLinkConfig
	if err := input.Decode(&config); err != nil {
		return err
	}
	remote, err := net.ResolveUDPAddr("udp4", config.Remote)
	if err != nil || !remote.IP.IsLoopback() {
		return errors.New("loopback peer required")
	}
	packet := &processUDPEndpoint{connection: connection, remote: remote}
	var transport PacketEndpoint = packet
	var paced *pacedFamilyEndpoint
	if config.Rate > 0 {
		paced = newPacedFamilyEndpoint(ctx, packet, config.Rate)
		transport = paced
		defer paced.Close()
	}
	reliability := reliablestream.DefaultConfig()
	reliability.SendWindow, reliability.ReceiveWindow = config.Window, config.Window
	session, err := OpenMuxReliable(ctx, transport, encoded(config.Profile), config.Server, true, reliability)
	if err != nil {
		return fmt.Errorf("Family TLS admission: %w", err)
	}
	defer session.Close()
	defer func() {
		if failure != nil {
			stats := session.ReliabilityStats()
			failure = fmt.Errorf("%w; reliable=%s retransmissions=%d flow=%+v events=%+v", failure, stats.Terminal, stats.Retransmissions, stats.Flow, stats.RecentEvents)
		}
	}()
	state := session.ConnectionState()
	if state.Version != tls.VersionTLS13 || state.NegotiatedProtocol != MuxCredit128Protocol || len(state.VerifiedChains) != 1 {
		return errors.New("verified Family TLS/mux contract missing")
	}
	completed := make(chan error, 1)
	if !config.Server {
		go func() {
			for index := range 8 {
				if err := session.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, 32768)); err != nil {
					completed <- err
					return
				}
			}
			completed <- nil
		}()
	}
	for index := range 8 {
		payload, err := session.Recv(ctx)
		if err != nil {
			return fmt.Errorf("payload%d receive: %w", index, err)
		}
		if !bytes.Equal(payload, bytes.Repeat([]byte{byte(index)}, 32768)) {
			return errors.New("payload mismatch")
		}
		if config.Server {
			if err := session.SendContext(ctx, payload); err != nil {
				return fmt.Errorf("payload%d echo: %w", index, err)
			}
		}
	}
	if !config.Server {
		if err := <-completed; err != nil {
			return err
		}
	}
	result := processLinkResult{Bytes: 8 * 32768, Retransmissions: session.ReliabilityStats().Retransmissions}
	if paced != nil {
		paced.mu.Lock()
		result.Drops = len(paced.dropped)
		paced.mu.Unlock()
	}
	if err := output.Encode(result); err != nil {
		return err
	}
	var closing string
	return input.Decode(&closing)
}

type processUDPEndpoint struct {
	connection *net.UDPConn
	remote     *net.UDPAddr
}

func (point *processUDPEndpoint) SendContext(ctx context.Context, payload []byte) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	deadline, _ := ctx.Deadline()
	point.connection.SetWriteDeadline(deadline)
	_, err := point.connection.WriteToUDP(payload, point.remote)
	return err
}

func (point *processUDPEndpoint) Recv(ctx context.Context) ([]byte, error) {
	deadline, _ := ctx.Deadline()
	point.connection.SetReadDeadline(deadline)
	buffer := make([]byte, reliablestream.HeaderSize+reliablestream.MaxPayload)
	for {
		count, sender, err := point.connection.ReadFromUDP(buffer)
		if err != nil {
			return nil, err
		}
		if sender.String() == point.remote.String() {
			return buffer[:count], nil
		}
	}
}

func (point *processUDPEndpoint) Close() error { return point.connection.Close() }

type pacedFamilyPacket struct {
	payload []byte
	ready   time.Time
}

type pacedFamilyEndpoint struct {
	PacketEndpoint
	ctx     context.Context
	cancel  context.CancelFunc
	done    chan struct{}
	queue   chan pacedFamilyPacket
	rate    int
	mu      sync.Mutex
	next    time.Time
	dropped map[uint64]bool
}

func newPacedFamilyEndpoint(ctx context.Context, underlying PacketEndpoint, rate int) *pacedFamilyEndpoint {
	ctx, cancel := context.WithCancel(ctx)
	point := &pacedFamilyEndpoint{PacketEndpoint: underlying, ctx: ctx, cancel: cancel, done: make(chan struct{}), queue: make(chan pacedFamilyPacket, 64), rate: rate, dropped: make(map[uint64]bool)}
	go func() {
		defer close(point.done)
		for {
			select {
			case packet := <-point.queue:
				timer := time.NewTimer(time.Until(packet.ready))
				select {
				case <-timer.C:
				case <-ctx.Done():
					timer.Stop()
					return
				}
				if err := underlying.SendContext(ctx, packet.payload); err != nil {
					cancel()
					underlying.Close()
					return
				}
			case <-ctx.Done():
				return
			}
		}
	}()
	return point
}

func (point *pacedFamilyEndpoint) SendContext(ctx context.Context, payload []byte) error {
	point.mu.Lock()
	defer point.mu.Unlock()
	if err := ctx.Err(); err != nil {
		return err
	}
	if point.next.Before(time.Now()) {
		point.next = time.Now()
	}
	point.next = point.next.Add(time.Duration((len(payload)+28)*8*115) * time.Second / time.Duration(point.rate*1000*100))
	sequence, isData := reliablestream.DataSequencePrefix(payload, uint32(len(payload)))
	if isData && sequence%17 == 0 && !point.dropped[sequence] {
		point.dropped[sequence] = true
		return nil
	}
	select {
	case point.queue <- pacedFamilyPacket{payload: bytes.Clone(payload), ready: point.next.Add(300 * time.Millisecond)}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-point.ctx.Done():
		return point.ctx.Err()
	default:
		return reliablestream.ErrBackpressure
	}
}

func (point *pacedFamilyEndpoint) Close() error {
	point.cancel()
	err := point.PacketEndpoint.Close()
	<-point.done
	return err
}
