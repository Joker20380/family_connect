package telemost

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"sync/atomic"
	"testing"
	"time"

	"github.com/pion/logging"
	"github.com/pion/transport/v4/vnet"
	"github.com/pion/webrtc/v4"
)

func TestICEPacketOutageRecoversMediaAndStillFailsPersistentLoss(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	logger := logging.NewDefaultLoggerFactory()
	logger.Writer = io.Discard
	router, err := vnet.NewRouter(&vnet.RouterConfig{CIDR: "10.77.0.0/24", LoggerFactory: logger})
	if err != nil {
		test.Fatal(err)
	}
	var blocked atomic.Bool
	router.AddChunkFilter(func(vnet.Chunk) bool { return !blocked.Load() })
	if err := router.Start(); err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { router.Stop() })
	var sessions [2]*Session
	var peers [2]*webrtc.PeerConnection
	var changes [2]chan webrtc.PeerConnectionState
	for index := range sessions {
		network, err := vnet.NewNet(&vnet.NetConfig{StaticIPs: []string{fmt.Sprintf("10.77.0.%d", index+1)}})
		if err != nil {
			test.Fatal(err)
		}
		if err := router.AddNet(network); err != nil {
			test.Fatal(err)
		}
		settings := webrtc.SettingEngine{}
		settings.SetNet(network)
		settings.SetNetworkTypes([]webrtc.NetworkType{webrtc.NetworkTypeUDP4})
		settings.SetICETimeouts(500*time.Millisecond, 3*time.Second, 100*time.Millisecond)
		settings.LoggerFactory = logger
		api := webrtc.NewAPI(webrtc.WithSettingEngine(settings))
		peer, err := api.NewPeerConnection(webrtc.Configuration{})
		if err != nil {
			test.Fatal(err)
		}
		session := testSession(test)
		session.pcPub.Store(peer)
		session.pcSub.Store(peer)
		states := make(chan webrtc.PeerConnectionState, 32)
		peer.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
			session.onSubscriberState(state)
			session.onPublisherState(state)
			states <- state
		})
		peer.OnICEConnectionStateChange(func(state webrtc.ICEConnectionState) { session.traceICE("SUBSCRIBER", state) })
		peer.OnTrack(session.onSubscriberTrack)
		if err := session.setupTransport(); err != nil {
			test.Fatal(err)
		}
		session.startWorker(session.writerLoop)
		sessions[index], peers[index], changes[index] = session, peer, states
	}
	for index, peer := range peers {
		var description webrtc.SessionDescription
		if index == 0 {
			description, err = peer.CreateOffer(nil)
		} else {
			description, err = peer.CreateAnswer(nil)
		}
		if err != nil {
			test.Fatal(err)
		}
		gathered := webrtc.GatheringCompletePromise(peer)
		if err := peer.SetLocalDescription(description); err != nil {
			test.Fatal(err)
		}
		select {
		case <-gathered:
		case <-ctx.Done():
			test.Fatal(ctx.Err())
		}
		if err := peers[1-index].SetRemoteDescription(*peer.LocalDescription()); err != nil {
			test.Fatal(err)
		}
	}
	wait := func(expected webrtc.PeerConnectionState) {
		test.Helper()
		for _, states := range changes {
			for {
				select {
				case state := <-states:
					if state == expected {
						goto reached
					}
					if state == webrtc.PeerConnectionStateFailed || state == webrtc.PeerConnectionStateClosed {
						test.Fatal("unexpected terminal state", state, expected)
					}
				case <-ctx.Done():
					test.Fatal("missing ICE transition", expected, ctx.Err())
				}
			}
		reached:
		}
	}
	transfer := func() {
		test.Helper()
		for index, sender := range sessions {
			payload := bytes.Repeat([]byte{byte(index + 1)}, 4096)
			if err := sender.SendContext(ctx, payload); err != nil {
				test.Fatal(err)
			}
			received, err := sessions[1-index].Recv(ctx)
			if err != nil || !bytes.Equal(received, payload) {
				test.Fatal("media did not recover byte-exact delivery", err)
			}
		}
	}
	wait(webrtc.PeerConnectionStateConnected)
	transfer()
	for range 2 {
		blocked.Store(true)
		wait(webrtc.PeerConnectionStateDisconnected)
		for _, session := range sessions {
			if session.closed.Load() || session.cfg.Trace.Snapshot().FirstFailure != nil {
				test.Fatal("transient packet loss terminated the media session")
			}
		}
		blocked.Store(false)
		wait(webrtc.PeerConnectionStateConnected)
		transfer()
	}
	blocked.Store(true)
	wait(webrtc.PeerConnectionStateFailed)
	for _, session := range sessions {
		if !session.closed.Load() {
			test.Fatal("persistent outage left a zombie carrier")
		}
	}
}
