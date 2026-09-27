package telemost

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/frame"
	"github.com/pion/webrtc/v4"
)

func TestLocalTwoProcessVP8(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
	defer cancel()
	initiator := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestLocalEndpointHelper$")
	responder := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestLocalEndpointHelper$")
	initiator.Env = append(os.Environ(), "FC_TEST_LOCAL_ENDPOINT=probe")
	responder.Env = append(os.Environ(), "FC_TEST_LOCAL_ENDPOINT=echo")
	initiatorIn, _ := initiator.StdinPipe()
	initiatorOut, _ := initiator.StdoutPipe()
	responderIn, _ := responder.StdinPipe()
	responderOut, _ := responder.StdoutPipe()
	var initiatorErrors, responderErrors bytes.Buffer
	initiator.Stderr = &initiatorErrors
	responder.Stderr = &responderErrors
	if err := initiator.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = initiator.Process.Kill(); _ = initiator.Wait() }()
	if err := responder.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = responder.Process.Kill(); _ = responder.Wait() }()
	offer, err := frame.ReadFrame(initiatorOut)
	if err != nil {
		t.Fatal(err)
	}
	if err := frame.WriteFrame(responderIn, offer); err != nil {
		t.Fatal(err)
	}
	answer, err := frame.ReadFrame(responderOut)
	if err != nil {
		t.Fatal(err)
	}
	if err := frame.WriteFrame(initiatorIn, answer); err != nil {
		t.Fatal(err)
	}
	result, err := frame.ReadFrame(initiatorOut)
	if err != nil || result.Opcode != frame.OpStatusResp || string(result.Payload) != "207 byte-for-byte checks" {
		t.Fatalf("local check failed: %v; probe=%s echo=%s", err, initiatorErrors.String(), responderErrors.String())
	}
	_ = frame.WriteFrame(responderIn, frame.Frame{Version: frame.Version, Opcode: frame.OpClose})
	if err := initiator.Wait(); err != nil {
		t.Fatal(err, initiatorErrors.String())
	}
	if err := responder.Wait(); err != nil {
		t.Fatal(err, responderErrors.String())
	}
	t.Log("PRELIMINARY ONLY: two local processes, real Pion VP8 RTP/DTLS, 7 sizes + 100x1KiB + 100x16KiB; NOT Telemost acceptance")
}

func TestLocalEndpointHelper(t *testing.T) {
	role := os.Getenv("FC_TEST_LOCAL_ENDPOINT")
	if role == "" {
		t.Skip("private subprocess helper")
	}
	if err := localEndpoint(role); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	os.Exit(0)
}

func localEndpoint(role string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Second)
	defer cancel()
	session, err := New(ctx, Config{RoomURL: "local-test"})
	if err != nil {
		return err
	}
	defer session.Close()
	api, err := newWebRTCAPI()
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
		encoded, err := json.Marshal(peer.LocalDescription())
		if err != nil {
			return err
		}
		return frame.WriteFrame(os.Stdout, frame.Frame{Version: frame.Version, Opcode: frame.OpOpen, Payload: encoded})
	}
	readDescription := func() error {
		message, err := frame.ReadFrame(os.Stdin)
		if err != nil {
			return err
		}
		var description webrtc.SessionDescription
		if err := json.Unmarshal(message.Payload, &description); err != nil {
			return err
		}
		return peer.SetRemoteDescription(description)
	}
	if role == "probe" {
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
	if role == "echo" {
		go func() { _, _ = frame.ReadFrame(os.Stdin); cancel() }()
		for {
			payload, err := session.Recv(ctx)
			if err != nil {
				if ctx.Err() != nil {
					return nil
				}
				return err
			}
			if err := session.Send(payload); err != nil {
				return err
			}
		}
	}
	sizes := []int{1, 32, 256, 1024, 4096, 16384, 65536}
	for range 100 {
		sizes = append(sizes, 1024)
	}
	for range 100 {
		sizes = append(sizes, 16384)
	}
	for _, size := range sizes {
		payload := make([]byte, size)
		if _, err := rand.Read(payload); err != nil {
			return err
		}
		requestContext, requestCancel := context.WithTimeout(ctx, 5*time.Second)
		err := session.SendContext(requestContext, payload)
		var received []byte
		if err == nil {
			received, err = session.Recv(requestContext)
		}
		requestCancel()
		if err != nil {
			return fmt.Errorf("size %d: %w", size, err)
		}
		if !bytes.Equal(payload, received) {
			return fmt.Errorf("size %d: mismatch", size)
		}
	}
	return frame.WriteFrame(os.Stdout, frame.Frame{Version: frame.Version, Opcode: frame.OpStatusResp, Payload: []byte("207 byte-for-byte checks")})
}
