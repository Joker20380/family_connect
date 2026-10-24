package tcpforward

import (
	"context"
	"encoding/json"
	"testing"
)

func TestSupportReasonPreservesLateFrameCounter(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 65536, ctx: ctx, cancel: cancel, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	mux.dispatchLocked(muxFrame{kind: resetFrame, id: 1})
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: []byte{1}})
	mux.dnsFrameLocked(dnsFrame(muxDNSError, 17, nil))
	if mux.stats.ProtocolErrors != 2 || mux.stats.ProtocolErrorReasons.UnknownStream != 1 || mux.stats.ProtocolErrorReasons.DNSUnmatched != 1 {
		test.Fatal("existing late-frame semantics/counters changed")
	}
	raw, err := json.Marshal(mux.stats.ProtocolErrorReasons)
	if err != nil || len(raw) > 256 {
		test.Fatal("bounded fixed reasons", err)
	}
}

func TestSupportInvalidDataReasonKeepsReset(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: []byte{1}})
	if stream.terminal != ErrProtocol || mux.stats.ProtocolErrors != 1 || mux.stats.ProtocolErrorReasons.DataState != 1 {
		test.Fatal("must reset invalid DATA, not hide error")
	}
}
