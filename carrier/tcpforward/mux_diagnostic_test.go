package tcpforward

import (
	"context"
	"io"
	"testing"
)

func TestTerminalPreservesFirstCauseAndTime(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, cancel: cancel, changed: make(chan struct{})}
	mux.fail(io.EOF)
	err, when := mux.Terminal()
	if err != io.EOF || when.IsZero() {
		test.Fatal("missing first terminal")
	}
	mux.fail(context.Canceled)
	later, at := mux.Terminal()
	if later != err || at != when {
		test.Fatal("cleanup replaced first failure")
	}
}

func TestControlOverflowRecordsTime(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, cancel: cancel, control: make([]muxFrame, 2*MuxMaxStreams+2*MuxMaxDNS)}
	mux.controlLocked(muxFrame{})
	err, when := mux.Terminal()
	if err != ErrProtocol || when.IsZero() {
		test.Fatal("missing overflow terminal")
	}
}
