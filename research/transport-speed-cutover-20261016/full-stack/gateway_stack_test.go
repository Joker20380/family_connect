package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/frame"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/pion/webrtc/v4"
	"golang.org/x/net/dns/dnsmessage"
)

type stackFault struct {
	*Session
	ctx          context.Context
	mu           sync.Mutex
	armed        bool
	scenario     string
	sequence     uint64
	chosen       bool
	first        time.Time
	retries      int
	firstRetryMS int64
	delivered    chan struct{}
	delayError   error
}

func (fault *stackFault) SendContext(ctx context.Context, payload []byte) error {
	fault.mu.Lock()
	data := len(payload) >= 64 && string(payload[:4]) == "FRS1" && payload[4] == 2
	if data && fault.chosen && binary.BigEndian.Uint64(payload[40:]) == fault.sequence {
		fault.retries++
		if fault.retries == 1 {
			fault.firstRetryMS = time.Since(fault.first).Milliseconds()
		}
	}
	if !fault.armed || fault.chosen || fault.scenario == "clean" || !data || len(payload) < 8192 {
		fault.mu.Unlock()
		return fault.Session.SendContext(ctx, payload)
	}
	fault.chosen = true
	fault.sequence = binary.BigEndian.Uint64(payload[40:])
	fault.first = time.Now()
	if fault.scenario == "loss" {
		fault.mu.Unlock()
		return nil
	}
	copyPayload := bytes.Clone(payload)
	fault.mu.Unlock()
	go func() {
		timer := time.NewTimer(400 * time.Millisecond)
		defer timer.Stop()
		var err error
		select {
		case <-timer.C:
			err = fault.Session.SendContext(fault.ctx, copyPayload)
		case <-fault.ctx.Done():
			err = fault.ctx.Err()
		}
		fault.mu.Lock()
		fault.delayError = err
		fault.mu.Unlock()
		close(fault.delivered)
	}()
	return nil
}

func (fault *stackFault) result(ctx context.Context) (map[string]any, error) {
	fault.mu.Lock()
	delayed := fault.chosen && fault.scenario == "reorder"
	fault.mu.Unlock()
	if delayed {
		select {
		case <-fault.delivered:
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	fault.mu.Lock()
	defer fault.mu.Unlock()
	return map[string]any{"injected": fault.chosen, "sequence": fault.sequence,
		"target_retransmissions": fault.retries, "first_retry_ms": fault.firstRetryMS}, fault.delayError
}

func stackWrite(value any) error {
	encoded, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return frame.WriteFrame(os.Stdout, frame.Frame{Version: frame.Version, Opcode: frame.OpStatusResp, Payload: encoded})
}

func stackRead(value any) error {
	message, err := frame.ReadFrame(os.Stdin)
	if err != nil {
		return err
	}
	return json.Unmarshal(message.Payload, value)
}

func TestFullStackChild(test *testing.T) {
	role := os.Getenv("FC_STACK_ROLE")
	if role == "" {
		test.Skip("private local subprocess fixture")
	}
	if err := stackChild(role); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	os.Exit(0)
}

func stackChild(role string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
	defer cancel()
	diagnostics := sessiontrace.New(strings.Repeat("a", 64), nil)
	session, err := New(ctx, Config{RoomURL: "local-test", Trace: diagnostics})
	if err != nil {
		return err
	}
	defer session.Close()
	api, err := diagnosticWebRTCAPI(nil, &boundaryFactory{trace: diagnostics, writes: &session.rtpWrites})
	if err != nil {
		return err
	}
	peer, err := api.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		return err
	}
	session.pcPub.Store(peer)
	session.pcSub.Store(peer)
	peer.OnTrack(session.onSubscriberTrack)
	peer.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
		session.onSubscriberState(state)
		session.onPublisherState(state)
	})
	if err := session.setupTransport(); err != nil {
		return err
	}
	session.startWorker(session.writerLoop)
	writeDescription := func(description webrtc.SessionDescription) error {
		gathered := webrtc.GatheringCompletePromise(peer)
		if err := peer.SetLocalDescription(description); err != nil {
			return err
		}
		select {
		case <-gathered:
		case <-ctx.Done():
			return ctx.Err()
		}
		return stackWrite(peer.LocalDescription())
	}
	readDescription := func() error {
		var description webrtc.SessionDescription
		if err := stackRead(&description); err != nil {
			return err
		}
		return peer.SetRemoteDescription(description)
	}
	if role == "client" {
		offer, err := peer.CreateOffer(nil)
		if err != nil {
			return err
		}
		if err := writeDescription(offer); err != nil {
			return err
		}
		if err := readDescription(); err != nil {
			return err
		}
	} else {
		if err := readDescription(); err != nil {
			return err
		}
		answer, err := peer.CreateAnswer(nil)
		if err != nil {
			return err
		}
		if err := writeDescription(answer); err != nil {
			return err
		}
	}
	select {
	case <-session.connected:
	case <-ctx.Done():
		return ctx.Err()
	case <-session.closeCh:
		return session.failure()
	}
	credentials, err := os.ReadFile(os.Getenv("FC_STACK_CREDENTIALS"))
	if err != nil {
		return err
	}
	fault := &stackFault{Session: session, ctx: ctx, scenario: os.Getenv("FC_STACK_SCENARIO"), delivered: make(chan struct{})}
	family, err := familysession.OpenReliable(ctx, fault, credentials, role == "server", reliablestream.DefaultConfig())
	if err != nil {
		return fmt.Errorf("family: %w", err)
	}
	defer family.Close()
	port := 0
	config := tcpforward.MuxConfig{}
	if role == "server" {
		listener, err := net.Listen("tcp4", "127.0.0.1:0")
		if err != nil {
			return err
		}
		defer listener.Close()
		port = listener.Addr().(*net.TCPAddr).Port
		config.Policy.TestOnlyLoopbackPort = port
		go func() {
			for {
				connection, err := listener.Accept()
				if err != nil {
					return
				}
				go func() {
					defer connection.Close()
					io.Copy(connection, connection)
				}()
			}
		}()
	}
	mux, err := tcpforward.NewMux(ctx, family, role == "server", config)
	if err != nil {
		return err
	}
	defer mux.Close()
	if role == "server" {
		tcpforward.ResearchFixtureDNS(mux)
	}
	if duplicate, err := tcpforward.NewMux(ctx, family, role == "server", config); err == nil {
		duplicate.Close()
		return fmt.Errorf("second mux owner accepted")
	}
	if err := stackWrite(map[string]any{"ready": true, "port": port}); err != nil {
		return err
	}
	var command struct{ Port int }
	if err := stackRead(&command); err != nil {
		return err
	}
	fault.mu.Lock()
	fault.armed = true
	fault.mu.Unlock()
	if role == "server" {
		if err := stackWrite(map[string]bool{"armed": true}); err != nil {
			return err
		}
		if err := stackRead(&command); err != nil {
			return err
		}
	} else {
		port = command.Port
		started := time.Now()
		if err := stackTraffic(ctx, mux, port); err != nil {
			return err
		}
		if err := stackWrite(map[string]any{"traffic_complete": true, "elapsed_ms": time.Since(started).Milliseconds(),
			"bulk_echo_bytes": 2 * 512 * 1024, "interactive_echoes": 8, "synthetic_dns_answers": 8}); err != nil {
			return err
		}
		if err := stackRead(&command); err != nil {
			return err
		}
	}
	faultResult, err := fault.result(ctx)
	if err != nil {
		return err
	}
	media := session.Stats()
	reliable := family.ReliabilityStats()
	if media.Media.RTPReceived == 0 || session.rtpWrites.Load() == 0 || reliable.Terminal != "" {
		return fmt.Errorf("missing RTP evidence or unexpected reliable terminal: %s", reliable.Terminal)
	}
	if err := stackWrite(map[string]any{"fault": faultResult, "retransmissions": reliable.Retransmissions,
		"duplicates": reliable.Duplicates, "recovered_gaps": reliable.RecoveredGaps,
		"rtp_received": media.Media.RTPReceived, "rtp_written": session.rtpWrites.Load(),
		"mux": mux.Stats()}); err != nil {
		return err
	}
	return stackRead(&command)
}

func stackTraffic(ctx context.Context, mux *tcpforward.Mux, port int) error {
	results := make(chan error, 3)
	for index := 0; index < 2; index++ {
		go func(index int) {
			payload := make([]byte, 512*1024)
			for position := range payload {
				payload[position] = byte((position*31 + index*17) % 251)
			}
			results <- stackEcho(ctx, mux, port, payload)
		}(index)
	}
	go func() {
		for index := 0; index < 8; index++ {
			if err := stackEcho(ctx, mux, port, []byte(fmt.Sprintf("interactive-%d", index))); err != nil {
				results <- err
				return
			}
			name, _ := dnsmessage.NewName("fixture.example.invalid.")
			question := dnsmessage.Message{Header: dnsmessage.Header{ID: uint16(index + 1)},
				Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}
			query, err := question.Pack()
			if err != nil {
				results <- err
				return
			}
			response, err := mux.QueryDNS(ctx, query)
			if err != nil {
				results <- err
				return
			}
			var answer dnsmessage.Message
			if err := answer.Unpack(response); err != nil || answer.ID != question.ID || len(answer.Answers) != 1 {
				results <- fmt.Errorf("DNS mismatch: %v", err)
				return
			}
			address, ok := answer.Answers[0].Body.(*dnsmessage.AResource)
			if !ok || address.A != [4]byte{192, 0, 2, 1} {
				results <- fmt.Errorf("DNS address mismatch")
				return
			}
		}
		results <- nil
	}()
	for range 3 {
		if err := <-results; err != nil {
			return err
		}
	}
	return nil
}

func stackEcho(ctx context.Context, mux *tcpforward.Mux, port int, payload []byte) error {
	stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: port})
	if err != nil {
		return err
	}
	defer stream.Close()
	sent := make(chan error, 1)
	go func() {
		_, err := stream.Write(payload)
		if err == nil {
			err = stream.CloseWrite()
		}
		sent <- err
	}()
	received, err := io.ReadAll(stream)
	if err != nil {
		return err
	}
	if err := <-sent; err != nil {
		return err
	}
	if !bytes.Equal(received, payload) {
		return fmt.Errorf("byte mismatch expected=%d received=%d", len(payload), len(received))
	}
	return nil
}

type stackProcess struct {
	command *exec.Cmd
	input   io.WriteCloser
	output  io.ReadCloser
	errors  bytes.Buffer
}

func stackStart(test *testing.T, ctx context.Context, binaryPath, role, scenario, credentials string) *stackProcess {
	test.Helper()
	process := &stackProcess{command: exec.CommandContext(ctx, binaryPath, "-test.run=^TestFullStackChild$")}
	process.command.Env = append(os.Environ(), "FC_STACK_ROLE="+role, "FC_STACK_SCENARIO="+scenario, "FC_STACK_CREDENTIALS="+credentials)
	process.input, _ = process.command.StdinPipe()
	process.output, _ = process.command.StdoutPipe()
	process.command.Stderr = &process.errors
	if err := process.command.Start(); err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { process.command.Process.Kill(); process.command.Wait() })
	return process
}

func (process *stackProcess) read(test *testing.T) frame.Frame {
	test.Helper()
	message, err := frame.ReadFrame(process.output)
	if err != nil {
		test.Fatal("child frame:", err)
	}
	return message
}

func (process *stackProcess) write(test *testing.T, message frame.Frame) {
	test.Helper()
	if err := frame.WriteFrame(process.input, message); err != nil {
		test.Fatal(err)
	}
}

func (process *stackProcess) send(test *testing.T, value any) {
	test.Helper()
	payload, err := json.Marshal(value)
	if err != nil {
		test.Fatal(err)
	}
	process.write(test, frame.Frame{Version: frame.Version, Opcode: frame.OpStatusResp, Payload: payload})
}

func TestFullStackMatrix(test *testing.T) {
	for _, clientVariant := range []string{"baseline", "candidate"} {
		for _, serverVariant := range []string{"baseline", "candidate"} {
			for _, scenario := range []string{"clean", "loss", "reorder"} {
				test.Run(clientVariant+"-"+serverVariant+"-"+scenario, func(test *testing.T) {
					ctx, cancel := context.WithTimeout(context.Background(), 40*time.Second)
					defer cancel()
					clientJSON, serverJSON := testCredentials(test)
					temporary := test.TempDir()
					for role, data := range map[string][]byte{"client": clientJSON, "server": serverJSON} {
						if err := os.WriteFile(filepath.Join(temporary, role), data, 0600); err != nil {
							test.Fatal(err)
						}
					}
					client := stackStart(test, ctx, os.Getenv("FC_STACK_"+strings.ToUpper(clientVariant)), "client", scenario, filepath.Join(temporary, "client"))
					server := stackStart(test, ctx, os.Getenv("FC_STACK_SERVER_"+strings.ToUpper(serverVariant)), "server", scenario, filepath.Join(temporary, "server"))
					defer func() {
						if test.Failed() {
							client.command.Process.Kill()
							server.command.Process.Kill()
							client.command.Wait()
							server.command.Wait()
							test.Log("client stderr:", client.errors.String(), "server stderr:", server.errors.String())
						}
					}()
					server.write(test, client.read(test))
					client.write(test, server.read(test))
					client.read(test)
					var ready struct {
						Ready bool
						Port  int
					}
					if err := json.Unmarshal(server.read(test).Payload, &ready); err != nil || !ready.Ready || ready.Port == 0 {
						test.Fatal("server not ready", err)
					}
					server.send(test, map[string]int{"port": ready.Port})
					server.read(test)
					client.send(test, map[string]int{"port": ready.Port})
					traffic := client.read(test).Payload
					client.send(test, map[string]int{})
					server.send(test, map[string]int{})
					clientResult := client.read(test).Payload
					serverResult := server.read(test).Payload
					for _, result := range [][]byte{clientResult, serverResult} {
						var parsed struct {
							Fault struct {
								Injected              bool
								TargetRetransmissions int `json:"target_retransmissions"`
							}
						}
						if err := json.Unmarshal(result, &parsed); err != nil {
							test.Fatal(err)
						}
						if scenario != "clean" && !parsed.Fault.Injected {
							test.Fatal("fault not exercised")
						}
						if scenario == "loss" && parsed.Fault.TargetRetransmissions == 0 {
							test.Fatal("loss not recovered")
						}
					}
					client.send(test, map[string]int{})
					server.send(test, map[string]int{})
					for _, process := range []*stackProcess{client, server} {
						if err := process.command.Wait(); err != nil {
							test.Fatal(err, process.errors.String())
						}
					}
					test.Logf("STACK_RESULT client=%s server=%s scenario=%s traffic=%s client_result=%s server_result=%s", clientVariant, serverVariant, scenario, traffic, clientResult, serverResult)
				})
				if test.Failed() {
					return
				}
			}
		}
	}
}
