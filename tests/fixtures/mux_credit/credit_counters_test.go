package tcpforward

import (
	"context"
	"encoding/binary"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestCreditCounterConservation(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, cancel: cancel, streams: make(map[uint32]*MuxStream), changed: make(chan struct{}), perf: &sessiontrace.MuxPerformance{}}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: make([]byte, 4096)})
	buffer := make([]byte, 1024)
	if count, err := stream.Read(buffer); err != nil || count != len(buffer) {
		test.Fatal(count, err)
	}
	if stream.used != 3072 || stream.receiveCredit != MuxWindow-3072 || stream.creditPending != 1024 {
		test.Fatal("credit conservation")
	}
	frame, ok := mux.pickLocked(false)
	if !ok || frame.kind != muxWindowUpdate || binary.BigEndian.Uint32(frame.payload) != 1024 || stream.creditPending != 0 || stream.perf.CreditReturns != 1 {
		test.Fatal("credit scheduler")
	}
	stream.sendCredit = 0
	stream.creditAt = time.Now().Add(-10 * time.Millisecond)
	mux.dispatchLocked(frame)
	if stream.sendCredit != 1024 || stream.perf.CreditUpdates != 1 || stream.perf.CreditIncrements.Bytes[1] != 1024 || stream.perf.CreditIntervals.TotalNS == 0 {
		test.Fatal("credit metrics")
	}
	stream.sendCredit = MuxWindow
	mux.dispatchLocked(frame)
	if stream.terminal == nil || mux.stats.ProtocolErrors != 1 {
		test.Fatal("overflow validation bypassed")
	}
}
