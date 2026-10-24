package tcpforward

import (
	"context"
	"testing"
)

func TestLifeLateControlAfterResetDoesNotChangeNeighbor(test *testing.T) {
	for _, kind := range []byte{muxWindowUpdate, closeFrame} {
		ctx, cancel := context.WithCancel(context.Background())
		mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
		stream := mux.makeStreamLocked(47)
		stream.opened = true
		neighbor := mux.makeStreamLocked(49)
		neighbor.opened = true
		stream.resetLocked(ErrReset)
		stream.send = nil
		mux.removeLocked(47)
		frame := muxFrame{kind: kind, id: 47}
		if kind == muxWindowUpdate {
			frame.payload = []byte{0, 0, 0, 24}
		}
		decoded, err := decodeMuxWindow(frame.encode(), 131072)
		if err != nil {
			test.Fatal(err)
		}
		credit := neighbor.sendCredit
		mux.dispatchLocked(decoded)
		incident := mux.lifeSnapshotLocked().FirstUnknown
		if incident == nil || !incident.Known || incident.Stream.Reason != "reset" || incident.Event.Kind != kind || incident.FailureAt != 0 {
			test.Fatal("missing late control history")
		}
		if neighbor.sendCredit != credit || neighbor.terminal != nil || mux.stats.ProtocolErrors != 1 || mux.streams[47] != nil {
			test.Fatal("changed stream state or hid raw event")
		}
		frame.payload = []byte{1}
		if _, err := decodeMuxWindow(frame.encode(), 131072); err != ErrProtocol {
			test.Fatal("malformed control accepted")
		}
		cancel()
	}
}
