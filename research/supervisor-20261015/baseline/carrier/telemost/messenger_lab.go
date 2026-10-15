//go:build fc_messenger_lab

package telemost

import (
	"context"

	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/pion/webrtc/v4"
)

func MessengerLabPeer(ctx context.Context, network *underlay.Network) (*Session, *webrtc.PeerConnection, error) {
	session, err := New(ctx, Config{RoomURL: "local-messenger", Mode: ModeVP8})
	if err != nil {
		return nil, nil, err
	}
	api, err := diagnosticWebRTCAPI(network, nil)
	if err != nil {
		session.Close()
		return nil, nil, err
	}
	peer, err := api.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		session.Close()
		return nil, nil, err
	}
	session.pcPub.Store(peer)
	session.pcSub.Store(peer)
	peer.OnTrack(session.onSubscriberTrack)
	peer.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
		session.onSubscriberState(state)
		session.onPublisherState(state)
	})
	if err := session.setupTransport(); err != nil {
		session.Close()
		return nil, nil, err
	}
	session.startWorker(session.writerLoop)
	return session, peer, nil
}

func MessengerLabDescription(ctx context.Context, peer *webrtc.PeerConnection, offer bool) (*webrtc.SessionDescription, error) {
	var description webrtc.SessionDescription
	var err error
	if offer {
		description, err = peer.CreateOffer(nil)
	} else {
		description, err = peer.CreateAnswer(nil)
	}
	if err != nil {
		return nil, err
	}
	gathered := webrtc.GatheringCompletePromise(peer)
	if err := peer.SetLocalDescription(description); err != nil {
		return nil, err
	}
	select {
	case <-gathered:
		return peer.LocalDescription(), nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (session *Session) MessengerLabConnected(ctx context.Context) error {
	select {
	case <-session.connected:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
