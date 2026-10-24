package tcpforward

import (
	"bytes"
	"context"
	"testing"
)

func TestLifeCrossedResetAfterLocalRemoval(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(91)
	stream.opened = true
	mux.lifeLocked("opened", 91, openOK, "peer")
	neighbor := mux.makeStreamLocked(93)
	neighbor.opened = true
	stream.resetLocked(ErrReset)
	if len(stream.send) != 1 || stream.send[0].kind != resetFrame {
		test.Fatal("missing local reset")
	}
	stream.send = nil
	mux.lifeLocked("send_done", 91, resetFrame, "local")
	mux.removeLocked(91)
	mux.dispatchLocked(muxFrame{kind: resetFrame, id: 91})
	incident := mux.lifeSnapshotLocked().FirstUnknown
	if incident == nil || !incident.Known || incident.Stream.Reason != "reset" || incident.Event.Kind != resetFrame || incident.Stream.Removed > incident.Event.At || incident.FailureAt != 0 || incident.Cancelled {
		test.Fatal("crossed reset provenance", incident)
	}
	if stream.receive != nil || stream.send != nil || stream.used != 0 || mux.streams[91] != nil {
		test.Fatal("retained retired stream")
	}
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 93, payload: []byte("neighbor intact")})
	buffer := make([]byte, 15)
	count, err := neighbor.Read(buffer)
	if err != nil || !bytes.Equal(buffer[:count], []byte("neighbor intact")) {
		test.Fatal("neighbor corrupted", err)
	}
	if mux.stats.ProtocolErrors != 1 || mux.stats.ProtocolErrorReasons.UnknownStream != 1 {
		test.Fatal("raw history rewritten")
	}
	mux.dispatchLocked(muxFrame{kind: resetFrame, id: 999})
	mux.dispatchLocked(muxFrame{kind: openOK, id: 93})
	if mux.stats.ProtocolErrors != 3 || neighbor.terminal != ErrProtocol {
		test.Fatal("real violations hidden")
	}
}
