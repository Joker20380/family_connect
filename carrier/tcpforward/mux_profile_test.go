package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"io"
	"testing"
)

func TestMux128RingCreditAndWrap(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	payload := bytes.Repeat([]byte{37}, MaxData)
	for index := 0; index < 8; index++ {
		mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: payload})
	}
	if stream.used != 131072 || stream.receiveCredit != 0 || stream.creditPending != 0 {
		test.Fatal("ring credit not conserved")
	}
	buffer := make([]byte, 3*MaxData)
	if _, err := io.ReadFull(stream, buffer); err != nil || !bytes.Equal(buffer, bytes.Repeat([]byte{37}, len(buffer))) {
		test.Fatal("initial read", err)
	}
	frame, ok := mux.pickLocked(false)
	if !ok || frame.kind != muxWindowUpdate || binary.BigEndian.Uint32(frame.payload) != uint32(len(buffer)) {
		test.Fatal("freed capacity not returned")
	}
	for index := 0; index < 3; index++ {
		mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: payload})
	}
	buffer = make([]byte, 131072)
	if _, err := io.ReadFull(stream, buffer); err != nil || !bytes.Equal(buffer, bytes.Repeat([]byte{37}, len(buffer))) {
		test.Fatal("wrapped read", err)
	}
	if stream.used != 0 || stream.receiveCredit != 131072 || stream.creditPending != 131072 {
		test.Fatal("full conservation")
	}
	frame, ok = mux.pickLocked(false)
	if !ok {
		test.Fatal("missing update")
	}
	if _, err := decodeMuxWindow(frame.encode(), 131072); err != nil {
		test.Fatal(err)
	}
	if _, err := decodeMux(frame.encode()); err == nil {
		test.Fatal("legacy accepted excess credit")
	}
	stream.sendCredit = 0
	mux.dispatchLocked(frame)
	if stream.sendCredit != 131072 {
		test.Fatal("wrong send capacity")
	}
	mux.dispatchLocked(frame)
	if stream.terminal == nil || mux.stats.ProtocolErrors != 1 {
		test.Fatal("credit overflow accepted")
	}
}

func TestMux128DataOverflowAndInvalidUpdate(test *testing.T) {
	for _, value := range []uint32{0, 131073, 0xffffffff} {
		payload := make([]byte, 4)
		binary.BigEndian.PutUint32(payload, value)
		if _, err := decodeMuxWindow((muxFrame{kind: muxWindowUpdate, id: 1, payload: payload}).encode(), 131072); err == nil {
			test.Fatal(value)
		}
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{window: 131072, ctx: ctx, cancel: cancel, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	for index := 0; index < 9; index++ {
		mux.dispatchLocked(muxFrame{kind: dataFrame, id: 1, payload: make([]byte, MaxData)})
	}
	if stream.terminal == nil || mux.stats.ProtocolErrors != 1 {
		test.Fatal("receive overflow accepted")
	}
}
