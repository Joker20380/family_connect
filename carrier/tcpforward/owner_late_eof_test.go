package tcpforward

import (
	"context"
	"io"
	"testing"
)

func TestLifeLateResetAfterClosedEOF(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, server: true, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(51)
	stream.opened = true
	stream.localFIN = true
	stream.remoteFIN = true
	neighbor := mux.makeStreamLocked(53)
	neighbor.opened = true
	stream.finishLocked(io.EOF)
	mux.removeLocked(51)
	mux.dispatchLocked(muxFrame{kind: resetFrame, id: 51})
	incident := mux.lifeSnapshotLocked().FirstUnknown
	if incident == nil || !incident.Known || incident.Stream.Reason != "eof" || !incident.Stream.LocalFIN || !incident.Stream.RemoteFIN || incident.Stream.Used != 0 {
		test.Fatal("lost completed-stream provenance")
	}
	if mux.stats.ProtocolErrors != 1 || neighbor.terminal != nil || mux.streams[51] != nil {
		test.Fatal("late reset changed a live stream or hid the counter")
	}
}
