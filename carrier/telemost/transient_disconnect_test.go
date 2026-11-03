package telemost

import (
	"context"
	"errors"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/webrtc/v4"
)

func TestTransientDisconnectPreservesEstablishedCarrier(test *testing.T) {
	for _, target := range []string{"SUBSCRIBER", "PUBLISHER", "BOTH"} {
		test.Run(target, func(test *testing.T) {
			session := testSession(test)
			session.cfg.Trace = sessiontrace.New(strings.Repeat("a", 64), nil)
			session.onSubscriberState(webrtc.PeerConnectionStateConnected)
			session.onPublisherState(webrtc.PeerConnectionStateConnected)
			for range 3 {
				if target != "PUBLISHER" {
					session.traceICE("SUBSCRIBER", webrtc.ICEConnectionStateDisconnected)
					session.onSubscriberState(webrtc.PeerConnectionStateDisconnected)
				}
				if target != "SUBSCRIBER" {
					session.traceICE("PUBLISHER", webrtc.ICEConnectionStateDisconnected)
					session.onPublisherState(webrtc.PeerConnectionStateDisconnected)
				}
				if session.closed.Load() || session.cfg.Trace.Snapshot().FirstFailure != nil {
					test.Fatal("recoverable ICE disruption terminated or poisoned the session")
				}
				if err := session.SendContext(context.Background(), []byte("synthetic encrypted frame")); err != nil {
					test.Fatal("established sender rejected a temporary disruption", err)
				}
				session.onSubscriberState(webrtc.PeerConnectionStateConnected)
				session.onPublisherState(webrtc.PeerConnectionStateConnected)
				if !session.subReady.Load() || !session.pubReady.Load() {
					test.Fatal("carrier readiness did not recover")
				}
			}
			session.traceICE("PUBLISHER", webrtc.ICEConnectionStateFailed)
			session.onPublisherState(webrtc.PeerConnectionStateFailed)
			if !session.closed.Load() || session.cfg.Trace.Snapshot().FirstFailure.Reason != "ICE_FAILED" {
				test.Fatal("persistent ICE failure no longer terminates precisely")
			}
		})
	}
}

func TestTransientDisconnectCannotCreateInitialReadiness(test *testing.T) {
	session := testSession(test)
	session.onSubscriberState(webrtc.PeerConnectionStateConnected)
	session.onSubscriberState(webrtc.PeerConnectionStateDisconnected)
	session.onPublisherState(webrtc.PeerConnectionStateConnected)
	select {
	case <-session.connected:
		test.Fatal("disconnected peer completed initial establishment")
	default:
	}
	if session.SendContext(context.Background(), []byte{1}) == nil {
		test.Fatal("unestablished transport accepted data")
	}
}

func TestTransientDisconnectRetainsCancellationAndTerminalClose(test *testing.T) {
	for _, terminal := range []webrtc.PeerConnectionState{webrtc.PeerConnectionStateFailed, webrtc.PeerConnectionStateClosed} {
		for _, target := range []string{"SUBSCRIBER", "PUBLISHER"} {
			session := testSession(test)
			session.onSubscriberState(webrtc.PeerConnectionStateConnected)
			session.onPublisherState(webrtc.PeerConnectionStateConnected)
			transition := session.onSubscriberState
			if target == "PUBLISHER" {
				transition = session.onPublisherState
			}
			transition(webrtc.PeerConnectionStateDisconnected)
			ctx, cancel := context.WithCancel(context.Background())
			cancel()
			if !errors.Is(session.SendContext(ctx, []byte{1}), context.Canceled) {
				test.Fatal("disruption bypassed caller cancellation")
			}
			transition(terminal)
			if !session.closed.Load() || !errors.Is(session.SendContext(context.Background(), []byte{1}), ErrClosed) {
				test.Fatal("terminal peer state failed to close carrier", target, terminal)
			}
		}
	}
}
