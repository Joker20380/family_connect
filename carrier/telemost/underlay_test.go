package telemost

import (
	"bytes"
	"context"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/pion/stun/v3"
	"github.com/pion/webrtc/v4"
)

func TestICECandidatesUseOnlyProtectedRoute(test *testing.T) {
	stunServer, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		test.Fatal(err)
	}
	stopped := make(chan struct{})
	go func() {
		defer close(stopped)
		buffer := make([]byte, 1500)
		for {
			count, remote, err := stunServer.ReadFromUDP(buffer)
			if err != nil {
				return
			}
			request := &stun.Message{Raw: append([]byte(nil), buffer[:count]...)}
			if request.Decode() != nil || request.Type != stun.BindingRequest {
				continue
			}
			response, err := stun.Build(stun.NewTransactionIDSetter(request.TransactionID), stun.BindingSuccess,
				&stun.XORMappedAddress{IP: remote.IP, Port: remote.Port})
			if err == nil {
				_, _ = stunServer.WriteToUDP(response.Raw, remote)
			}
		}
	}()
	test.Cleanup(func() { _ = stunServer.Close(); <-stopped })
	network, err := underlay.New(context.Background(), "127.0.0.1:53", func(int) bool { return true })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	interfaces, err := network.Interfaces()
	if err != nil || len(interfaces) == 0 {
		test.Fatal("missing test interface", err)
	}
	interfaces[0].AddAddress(&net.IPNet{IP: net.IPv4(127, 0, 0, 2), Mask: net.CIDRMask(8, 32)})
	settings, err := webRTCSettings(network)
	if err != nil {
		test.Fatal(err)
	}
	settings.SetIncludeLoopbackCandidate(true)
	peer, err := webrtc.NewAPI(webrtc.WithSettingEngine(settings)).NewPeerConnection(webrtc.Configuration{
		ICEServers: []webrtc.ICEServer{{URLs: []string{fmt.Sprintf("stun:%s", stunServer.LocalAddr())}}},
	})
	if err != nil {
		test.Fatal(err)
	}
	defer peer.Close()
	if _, err := peer.CreateDataChannel("route-test", nil); err != nil {
		test.Fatal(err)
	}
	candidates := make(chan *webrtc.ICECandidate, 256)
	peer.OnICECandidate(func(candidate *webrtc.ICECandidate) { candidates <- candidate })
	offer, err := peer.CreateOffer(nil)
	if err != nil {
		test.Fatal(err)
	}
	if err := peer.SetLocalDescription(offer); err != nil {
		test.Fatal(err)
	}
	deadline := time.After(5 * time.Second)
	hosts, reflexive := 0, 0
	for {
		select {
		case candidate := <-candidates:
			if candidate == nil {
				if hosts == 0 || reflexive == 0 {
					test.Fatal("missing protected-route host or STUN candidate")
				}
				return
			}
			if candidate.Typ == webrtc.ICECandidateTypeHost {
				hosts++
			}
			if candidate.Typ == webrtc.ICECandidateTypeSrflx {
				reflexive++
			}
			if !net.ParseIP(candidate.Address).Equal(net.IPv4(127, 0, 0, 1)) {
				test.Fatal("ICE advertised an interface outside the protected route")
			}
		case <-deadline:
			test.Fatal("ICE gathering did not finish")
		}
	}
}

func TestICERouteCannotBypassDeniedOrClosedProtection(test *testing.T) {
	for _, scenario := range []string{"denied", "closed", "cancelled"} {
		test.Run(scenario, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			network, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { return scenario != "denied" })
			if err != nil {
				test.Fatal(err)
			}
			defer network.Close()
			if scenario == "closed" {
				network.Close()
			}
			if scenario == "cancelled" {
				cancel()
			}
			if _, err := diagnosticWebRTCAPI(network, nil); err == nil {
				test.Fatal("ICE initialized without a protected route")
			}
		})
	}
}

func TestProtectedRouteCarriesBidirectionalVP8(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	var sessions [2]*Session
	var peers [2]*webrtc.PeerConnection
	ready := make(chan struct{}, 2)
	for index := range sessions {
		network, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { return true })
		if err != nil {
			test.Fatal(err)
		}
		test.Cleanup(network.Close)
		settings, err := webRTCSettings(network)
		if err != nil {
			test.Fatal(err)
		}
		settings.SetIncludeLoopbackCandidate(true)
		peer, err := webrtc.NewAPI(webrtc.WithSettingEngine(settings)).NewPeerConnection(webrtc.Configuration{})
		if err != nil {
			test.Fatal(err)
		}
		session := testSession(test)
		session.pcPub.Store(peer)
		session.pcSub.Store(peer)
		peer.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
			session.onSubscriberState(state)
			session.onPublisherState(state)
			if state == webrtc.PeerConnectionStateConnected {
				select {
				case ready <- struct{}{}:
				case <-ctx.Done():
				}
			}
		})
		peer.OnTrack(session.onSubscriberTrack)
		if err := session.setupTransport(); err != nil {
			test.Fatal(err)
		}
		session.startWorker(session.writerLoop)
		sessions[index], peers[index] = session, peer
	}
	for index, peer := range peers {
		var description webrtc.SessionDescription
		var err error
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
			test.Fatal("protected ICE gathering timed out")
		}
		if err := peers[1-index].SetRemoteDescription(*peer.LocalDescription()); err != nil {
			test.Fatal(err)
		}
	}
	for range 2 {
		select {
		case <-ready:
		case <-ctx.Done():
			test.Fatal("protected ICE connection timed out")
		}
	}
	for index, sender := range sessions {
		for _, size := range []int{1, 4096, 65536} {
			payload := bytes.Repeat([]byte{byte(index + 1)}, size)
			if err := sender.SendContext(ctx, payload); err != nil {
				test.Fatal(err)
			}
			received, err := sessions[1-index].Recv(ctx)
			if err != nil || !bytes.Equal(received, payload) {
				test.Fatal("protected-route VP8 delivery was not byte-exact", err)
			}
		}
	}
}

func TestRestrictedHTTPAndWebSocketCannotBypassProtection(test *testing.T) {
	server := httptest.NewServer(http.NotFoundHandler())
	defer server.Close()
	network, err := underlay.New(context.Background(), "127.0.0.1:53", func(int) bool { return false })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	session, err := New(context.Background(), Config{RoomURL: "test-room", Underlay: network, HTTPClient: server.Client()})
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	if response, err := session.auth.Client.Get(server.URL); err == nil {
		response.Body.Close()
		test.Fatal("custom HTTP client bypassed protected network")
	}
	session.wsURL = "ws" + strings.TrimPrefix(server.URL, "http")
	if err := session.dialWebSocket(context.Background()); err == nil {
		test.Fatal("WebSocket bypassed protected network")
	}
	if network.Rejected.Load() != 2 || network.Protected.Load() != 0 {
		test.Fatal("signaling protection paths not enforced")
	}
}
