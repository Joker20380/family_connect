// Package frame implements the private framed IPC contract between a parent
// process and the isolated WebRTC carrier process.
//
// Wire layout (big-endian):
//
//	u32be body_length | u8 version | u8 opcode | u32be request_id | payload
//
// body_length counts every byte after the length field itself
// (version + opcode + request_id + payload = 6 + len(payload)).
// Payload opcodes preserve exact bytes, including zero bytes.
package frame

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

const (
	// Version is the only protocol version understood by this codec.
	Version byte = 1

	// HeaderLen is the fixed length of a frame header (length field excluded).
	HeaderLen = 1 + 1 + 4 // version + opcode + request_id

	// MaxBodyLen bounds the total body (HeaderLen + payload).
	MaxBodyLen = HeaderLen + 64*1024

	// MaxPayloadLen is the largest payload a frame may carry.
	MaxPayloadLen = MaxBodyLen - HeaderLen

	// MaxControlJSONLen bounds the JSON carried by control opcodes.
	MaxControlJSONLen = 16 * 1024
)

// Opcodes. Commands are in the 0x01..0x3f range, events/responses in 0x80..0xbf.
const (
	OpOpen   byte = 0x01
	OpSend   byte = 0x02
	OpPing   byte = 0x03
	OpStatus byte = 0x04
	OpClose  byte = 0x05

	OpOpened     byte = 0x81
	OpRecv       byte = 0x82
	OpPong       byte = 0x83
	OpStatusResp byte = 0x84
	OpError      byte = 0x85
	OpClosed     byte = 0x86
)

// Frame is a decoded IPC frame.
type Frame struct {
	Version   byte
	Opcode    byte
	RequestID uint32
	Payload   []byte
}

var (
	// ErrTruncated is returned when a frame is too short or missing bytes.
	ErrTruncated = errors.New("frame: truncated frame")
	// ErrTooLarge is returned when a frame exceeds the negotiated bounds.
	ErrTooLarge = errors.New("frame: frame too large")
	// ErrBadVersion is returned for an unsupported protocol version.
	ErrBadVersion = errors.New("frame: unsupported version")
)

// Encode serialises a frame into a single contiguous byte slice.
func Encode(version, opcode byte, requestID uint32, payload []byte) ([]byte, error) {
	if version != Version {
		return nil, ErrBadVersion
	}
	if !validOpcode(opcode) {
		return nil, errors.New("frame: unsupported opcode")
	}
	if opcode != OpSend && opcode != OpRecv && len(payload) > MaxControlJSONLen {
		return nil, ErrTooLarge
	}
	if len(payload) > MaxPayloadLen {
		return nil, ErrTooLarge
	}
	bodyLen := HeaderLen + len(payload)
	out := make([]byte, 4+bodyLen)
	binary.BigEndian.PutUint32(out[0:4], uint32(bodyLen))
	out[4] = version
	out[5] = opcode
	binary.BigEndian.PutUint32(out[6:10], requestID)
	copy(out[10:], payload)
	return out, nil
}

// Decode parses a single complete frame from data. It rejects trailing bytes.
func Decode(data []byte) (Frame, error) {
	if len(data) < 4 {
		return Frame{}, ErrTruncated
	}
	bodyLen := int(binary.BigEndian.Uint32(data[0:4]))
	if bodyLen < HeaderLen {
		return Frame{}, ErrTruncated
	}
	if bodyLen > MaxBodyLen {
		return Frame{}, ErrTooLarge
	}
	total := 4 + bodyLen
	if len(data) < total {
		return Frame{}, ErrTruncated
	}
	if len(data) > total {
		return Frame{}, fmt.Errorf("frame: %d trailing bytes", len(data)-total)
	}
	f := Frame{
		Version:   data[4],
		Opcode:    data[5],
		RequestID: binary.BigEndian.Uint32(data[6:10]),
	}
	if f.Version != Version {
		return Frame{}, ErrBadVersion
	}
	if !validOpcode(f.Opcode) {
		return Frame{}, errors.New("frame: unsupported opcode")
	}
	if f.Opcode != OpSend && f.Opcode != OpRecv && bodyLen-HeaderLen > MaxControlJSONLen {
		return Frame{}, ErrTooLarge
	}
	if bodyLen > HeaderLen {
		f.Payload = append([]byte(nil), data[10:total]...)
	}
	return f, nil
}

// ReadFrame reads one frame from r. It reads the 4-byte length prefix, rejects
// out-of-range lengths before allocating, and then reads the body.
func ReadFrame(r io.Reader) (Frame, error) {
	var lenBuf [4]byte
	if _, err := io.ReadFull(r, lenBuf[:]); err != nil {
		return Frame{}, err
	}
	bodyLen := int(binary.BigEndian.Uint32(lenBuf[:]))
	if bodyLen < HeaderLen {
		return Frame{}, ErrTruncated
	}
	if bodyLen > MaxBodyLen {
		return Frame{}, ErrTooLarge
	}
	buf := make([]byte, bodyLen)
	if _, err := io.ReadFull(r, buf); err != nil {
		return Frame{}, err
	}
	full := make([]byte, 0, 4+bodyLen)
	full = append(full, lenBuf[:]...)
	full = append(full, buf...)
	return Decode(full)
}

// WriteFrame writes f to w as a single contiguous frame.
func WriteFrame(w io.Writer, f Frame) error {
	b, err := Encode(f.Version, f.Opcode, f.RequestID, f.Payload)
	if err != nil {
		return err
	}
	written, err := w.Write(b)
	if err == nil && written != len(b) {
		return io.ErrShortWrite
	}
	return err
}

func validOpcode(opcode byte) bool {
	return opcode >= OpOpen && opcode <= OpClose || opcode >= OpOpened && opcode <= OpClosed
}

// IsCommand reports whether opcode is a parent->carrier command.
func IsCommand(opcode byte) bool { return opcode >= 0x01 && opcode <= 0x3f }

// IsEvent reports whether opcode is a carrier->parent event/response.
func IsEvent(opcode byte) bool { return opcode >= 0x80 && opcode <= 0xbf }
