package telemost

import (
	"testing"

	"github.com/pion/webrtc/v4"
)

func TestRestartAuditPeerStateIsTerminalAndGenerationLocal(test *testing.T) {
	for _, target := range []string{"subscriber", "publisher"} {
		for _, state := range []webrtc.PeerConnectionState{webrtc.PeerConnectionStateDisconnected, webrtc.PeerConnectionStateFailed, webrtc.PeerConnectionStateClosed} {
			test.Run(target+"/"+state.String(), func(test *testing.T) {
				previous := testSession(test)
				replacement := testSession(test)
				callback := previous.onSubscriberState
				if target == "publisher" {
					callback = previous.onPublisherState
				}
				callback(webrtc.PeerConnectionStateConnected)
				callback(state)
				callback(webrtc.PeerConnectionStateConnected)
				if !previous.closed.Load() || previous.Send([]byte{1}) != ErrClosed {
					test.Fatal("terminal session resurrected")
				}
				if replacement.closed.Load() || replacement.disconnects.Load() != 0 {
					test.Fatal("old callback affected replacement")
				}
				if previous.disconnects.Load() != 1 {
					test.Fatal("duplicate close")
				}
			})
		}
	}
}
