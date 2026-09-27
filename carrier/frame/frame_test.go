package frame

import (
	"bytes"
	"io"
	"testing"
)

func TestEncodeDecodeRoundTrip(t *testing.T) {
	payload := []byte{0x00, 0x01, 0x02, 0xff, 0x00}
	b, err := Encode(Version, OpSend, 0x01020304, payload)
	if err != nil {
		t.Fatalf("encode: %v", err)
	}
	// 4 length + 1 version + 1 opcode + 4 request_id + 5 payload
	if len(b) != 4+HeaderLen+len(payload) {
		t.Fatalf("unexpected encoded length %d", len(b))
	}
	f, err := Decode(b)
	if err != nil {
		t.Fatalf("decode: %v", err)
	}
	if f.Version != Version || f.Opcode != OpSend || f.RequestID != 0x01020304 {
		t.Fatalf("bad header: %+v", f)
	}
	if !bytes.Equal(f.Payload, payload) {
		t.Fatalf("payload mismatch: %x", f.Payload)
	}
}

func TestDecodeRejectsOversizedLength(t *testing.T) {
	b := []byte{0xff, 0xff, 0xff, 0xff, Version, OpSend, 0, 0, 0, 0}
	if _, err := Decode(b); err != ErrTooLarge {
		t.Fatalf("expected ErrTooLarge, got %v", err)
	}
}

func TestDecodeRejectsBadVersion(t *testing.T) {
	b, _ := Encode(Version, OpSend, 1, nil)
	b[4] = 0x7f
	if _, err := Decode(b); err != ErrBadVersion {
		t.Fatalf("expected ErrBadVersion, got %v", err)
	}
}

func TestEncodeRejectsOversizedPayload(t *testing.T) {
	if _, err := Encode(Version, OpSend, 1, make([]byte, MaxPayloadLen+1)); err != ErrTooLarge {
		t.Fatalf("expected ErrTooLarge, got %v", err)
	}
}

func TestReadWriteFrame(t *testing.T) {
	payload := bytes.Repeat([]byte{0xaa}, 1000)
	var buf bytes.Buffer
	if err := WriteFrame(&buf, Frame{Version, OpRecv, 42, payload}); err != nil {
		t.Fatalf("write: %v", err)
	}
	f, err := ReadFrame(&buf)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if f.Opcode != OpRecv || f.RequestID != 42 || !bytes.Equal(f.Payload, payload) {
		t.Fatalf("bad round trip: %+v", f)
	}
}

func TestReadFrameRejectsOversizedLengthBeforeAlloc(t *testing.T) {
	r := bytes.NewReader([]byte{0xff, 0xff, 0xff, 0xff})
	if _, err := ReadFrame(r); err != ErrTooLarge {
		t.Fatalf("expected ErrTooLarge, got %v", err)
	}
}

func TestReadFrameEOF(t *testing.T) {
	if _, err := ReadFrame(bytes.NewReader(nil)); err != io.EOF {
		t.Fatalf("expected io.EOF, got %v", err)
	}
}

func TestOpcodeClassification(t *testing.T) {
	if !IsCommand(OpOpen) || !IsCommand(OpClose) {
		t.Fatal("commands not classified as commands")
	}
	if IsCommand(OpRecv) {
		t.Fatal("event classified as command")
	}
	if !IsEvent(OpRecv) || !IsEvent(OpError) {
		t.Fatal("events not classified as events")
	}
	if IsEvent(OpOpen) {
		t.Fatal("command classified as event")
	}
}

type shortWriter struct{}

func (shortWriter) Write(data []byte) (int, error) { return len(data) - 1, nil }

func TestFrameBoundaryAndShortWrite(t *testing.T) {
	payload := make([]byte, 65536)
	encoded, err := Encode(Version, OpSend, 1, payload)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Decode(encoded); err != nil {
		t.Fatal(err)
	}
	if err := WriteFrame(shortWriter{}, Frame{Version, OpSend, 1, payload}); err != io.ErrShortWrite {
		t.Fatal(err)
	}
	if _, err := Encode(Version, OpStatus, 1, payload); err != ErrTooLarge {
		t.Fatal(err)
	}
	if _, err := Encode(Version, 0x20, 1, nil); err == nil {
		t.Fatal("unknown opcode")
	}
	for index := 0; index < len(encoded); index += 1024 {
		if _, err := Decode(encoded[:index]); err == nil {
			t.Fatal("truncation")
		}
	}
}

func FuzzDecode(f *testing.F) {
	encoded, _ := Encode(Version, OpSend, 1, []byte{0, 255})
	f.Add(encoded)
	f.Fuzz(func(t *testing.T, data []byte) { _, _ = Decode(data) })
}
