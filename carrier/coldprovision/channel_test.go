package coldprovision

import (
	"bytes"
	"context"
	"encoding/binary"
	"testing"
)

func TestFramingRejectsAmbiguousOversizedAndTruncatedInput(test *testing.T) {
	for _, raw := range [][]byte{[]byte(`{"path":"one","path":"two"}`), []byte(`{"unknown":1}`), []byte(`{"path":"one"} {}`), bytes.Repeat([]byte("x"), MaxMessage+1)} {
		var request Request
		if strict(raw, &request) == nil {
			test.Fatal("unsafe JSON accepted")
		}
	}
	for _, size := range []uint32{0, MaxMessage + 1, 10} {
		var header [4]byte
		binary.BigEndian.PutUint32(header[:], size)
		var request Request
		if read(bytes.NewReader(header[:]), &request) == nil {
			test.Fatal("unsafe frame accepted")
		}
	}
}

func TestAdapterCannotBecomeProxyOrDataPlane(test *testing.T) {
	for _, address := range []string{"example.com:8443", "192.0.2.1:8443", "https://127.0.0.1:8443", "127.0.0.1:0", "127.0.0.1:65536"} {
		if _, err := LoopbackBackend(address); err == nil {
			test.Fatalf("unsafe backend accepted: %s", address)
		}
	}
	backend, err := LoopbackBackend("127.0.0.1:1")
	if err != nil {
		test.Fatal(err)
	}
	for _, path := range []string{"/friends/activate", "/friends/configuration/nl", "/dns-query", "/tcp", "https://example.com", "/friends/restricted-readiness/ack"} {
		if _, err := backend(context.Background(), Request{Path: path}); err == nil {
			test.Fatal("unsafe operation accepted")
		}
	}
}
