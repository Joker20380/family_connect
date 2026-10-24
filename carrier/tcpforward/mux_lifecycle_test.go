package tcpforward

import (
	"context"
	"encoding/json"
	"testing"
)

func TestLifeUnknownAfterResetAndNeverKnown(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	mux.lifeLocked("opened", 1, openOK, "peer")
	neighbor := mux.makeStreamLocked(3)
	neighbor.opened = true
	mux.dispatchLocked(muxFrame{kind: resetFrame, id: 1})
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: []byte{42}})
	snapshot := mux.lifeSnapshotLocked()
	incident := snapshot.FirstUnknown
	if incident == nil || !incident.Known || incident.Stream.ID != 1 || incident.Stream.Reason != "reset" || incident.Stream.Created == 0 || incident.Stream.Opened == 0 || incident.Stream.Removed < incident.Stream.Finished || incident.FailureAt != 0 || incident.Cancelled {
		test.Fatal("lost provenance", incident)
	}
	if mux.stats.ProtocolErrors != 1 || neighbor.terminal != nil {
		test.Fatal("observation changed behavior")
	}
	incident.Stream.ID = 99
	if mux.lifeSnapshotLocked().FirstUnknown.Stream.ID != 1 {
		test.Fatal("aliased incident")
	}
	mux.life.first = nil
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 101, payload: []byte{42}})
	if mux.lifeSnapshotLocked().FirstUnknown.Known {
		test.Fatal("invented stream history")
	}
}

func TestLifeBoundsAndFailureOrder(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, cancel: cancel, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	for index := uint32(1); index < 10000; index++ {
		stream := mux.makeStreamLocked(index)
		stream.finishLocked(ErrReset)
		mux.removeLocked(index)
	}
	mux.lifeLocked("failure", 0, 0, "closed_pipe")
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 9999, payload: []byte{1}})
	snapshot := mux.lifeSnapshotLocked()
	if len(snapshot.Events) != 32 || snapshot.Dropped == 0 || snapshot.FirstUnknown.FailureAt == 0 || len(mux.streams) != 0 {
		test.Fatal("unbounded or missing failure")
	}
	raw, err := json.Marshal(snapshot)
	if err != nil || len(raw) > 8192 {
		test.Fatal("export bound", len(raw), err)
	}
	snapshot.Events[0].Stage = "modified"
	if mux.lifeSnapshotLocked().Events[0].Stage == "modified" {
		test.Fatal("aliased ring")
	}
	mux.config.Lifecycle = false
	if mux.lifeSnapshotLocked() != nil {
		test.Fatal("disabled observer exported")
	}
}
