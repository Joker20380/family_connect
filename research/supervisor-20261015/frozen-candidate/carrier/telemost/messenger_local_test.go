package telemost

import (
	"context"
	"encoding/json"
	"io"
	"net"
	"net/netip"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/pion/webrtc/v4"
)

func messengerPeer(test *testing.T, ctx context.Context) (*Session, *webrtc.PeerConnection) {
	test.Helper()
	session, err := New(ctx, Config{RoomURL: "local-messenger", Mode: ModeVP8})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { session.Close() })
	api, err := diagnosticWebRTCAPI(nil, nil)
	if err != nil {
		test.Fatal(err)
	}
	peer, err := api.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		test.Fatal(err)
	}
	session.pcPub.Store(peer)
	session.pcSub.Store(peer)
	peer.OnTrack(session.onSubscriberTrack)
	peer.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
		session.onSubscriberState(state)
		session.onPublisherState(state)
	})
	if err := session.setupTransport(); err != nil {
		test.Fatal(err)
	}
	session.startWorker(session.writerLoop)
	return session, peer
}

func TestMessengerLocalProvider(test *testing.T) {
	directory := os.Getenv("FC_MESSENGER_LOCAL_FIXTURE")
	if directory == "" {
		test.Skip("disposable local provider only")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 180*time.Second)
	defer cancel()
	left, leftPeer := messengerPeer(test, ctx)
	right, rightPeer := messengerPeer(test, ctx)
	description := func(peer *webrtc.PeerConnection, remote *webrtc.PeerConnection, offer bool) {
		var value webrtc.SessionDescription
		var err error
		if offer {
			value, err = peer.CreateOffer(nil)
		} else {
			value, err = peer.CreateAnswer(nil)
		}
		if err != nil {
			test.Fatal(err)
		}
		gathered := webrtc.GatheringCompletePromise(peer)
		if err := peer.SetLocalDescription(value); err != nil {
			test.Fatal(err)
		}
		select {
		case <-gathered:
		case <-ctx.Done():
			test.Fatal(ctx.Err())
		}
		if err := remote.SetRemoteDescription(*peer.LocalDescription()); err != nil {
			test.Fatal(err)
		}
	}
	description(leftPeer, rightPeer, true)
	description(rightPeer, leftPeer, false)
	for _, session := range []*Session{left, right} {
		select {
		case <-session.connected:
		case <-ctx.Done():
			test.Fatal(ctx.Err())
		}
	}
	clientRaw, err := os.ReadFile(filepath.Join(directory, "valid.json"))
	if err != nil {
		test.Fatal(err)
	}
	serverRaw, err := os.ReadFile(filepath.Join(directory, "gateway.json"))
	if err != nil {
		test.Fatal(err)
	}
	defer clear(clientRaw)
	defer clear(serverRaw)
	type securedResult struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan securedResult, 1)
	go func() {
		session, err := familysession.Open(ctx, right, serverRaw, true)
		ready <- securedResult{session, err}
	}()
	client, err := familysession.Open(ctx, left, clientRaw, false)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	serverResult := <-ready
	if serverResult.err != nil {
		test.Fatal(serverResult.err)
	}
	defer serverResult.session.Close()
	target, err := netip.ParseAddrPort(os.Getenv("FC_MESSENGER_LOCAL_MAILBOX"))
	if err != nil || !target.Addr().IsLoopback() {
		test.Fatal("loopback mailbox fixture required")
	}
	server, err := tcpforward.NewMux(ctx, serverResult.session, true, tcpforward.MuxConfig{MaxStreams: 4,
		Policy: tcpforward.Policy{Services: map[string]netip.AddrPort{"chat-mailbox.family-connect.invalid": target}}})
	if err != nil {
		test.Fatal(err)
	}
	defer server.Close()
	mux, err := tcpforward.NewMux(ctx, client, false, tcpforward.MuxConfig{MaxStreams: 4})
	if err != nil {
		test.Fatal(err)
	}
	defer mux.Close()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	defer listener.Close()
	var workers sync.WaitGroup
	acceptDone := make(chan struct{})
	slots := make(chan struct{}, 3)
	go func() {
		defer close(acceptDone)
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			select {
			case slots <- struct{}{}:
			default:
				connection.Close()
				continue
			}
			workers.Add(1)
			go func() {
				defer workers.Done()
				defer func() { <-slots }()
				defer connection.Close()
				deadline, stop := context.WithTimeout(ctx, 30*time.Second)
				defer stop()
				stream, err := mux.OpenTCP(deadline, tcpforward.OpenRequest{Host: "chat-mailbox.family-connect.invalid", Port: 1})
				if err != nil {
					return
				}
				defer stream.Reset()
				closeConnection := context.AfterFunc(deadline, func() { connection.Close(); stream.Reset() })
				defer closeConnection()
				finished := make(chan struct{})
				go func() { io.Copy(stream, connection); stream.CloseWrite(); close(finished) }()
				io.Copy(connection, stream)
				connection.Close()
				<-finished
			}()
		}
	}()
	json.NewEncoder(os.Stdout).Encode(map[string]any{"address": listener.Addr().String(), "scope": "LOCAL_PION_FAMILY_TLS_MUX", "tun": false})
	buffer := make([]byte, 1)
	os.Stdin.Read(buffer)
	listener.Close()
	<-acceptDone
	cancel()
	workers.Wait()
	json.NewEncoder(os.Stdout).Encode(map[string]any{"client": mux.Stats(), "server": server.Stats(), "carrier": left.Stats()})
}
