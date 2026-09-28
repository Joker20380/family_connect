package tcpforward

import (
	"encoding/binary"
	"errors"
)

const MuxWindow = 64 << 10
const MuxMaxStreams = 32
const muxMaxID = 1<<31 - 1
const muxWindowUpdate byte = 8
const muxDNSQuery byte = 9
const muxDNSResponse byte = 10
const muxDNSError byte = 11
const muxDNSCancel byte = 12
const MuxMaxDNS = 16
const MuxMaxDNSMessage = 4096

var ErrStreamLimit = errors.New("mux stream limit reached")
var ErrIDExhausted = errors.New("mux ID space exhausted; open a fresh session")
var ErrDNS = errors.New("mux DNS failed")

type muxFrame struct {
	kind    byte
	id      uint32
	payload []byte
}

func (frame muxFrame) encode() []byte {
	encoded := make([]byte, headerSize+len(frame.payload))
	encoded[0], encoded[1] = 2, frame.kind
	binary.BigEndian.PutUint32(encoded[2:6], frame.id)
	binary.BigEndian.PutUint32(encoded[6:10], uint32(len(frame.payload)))
	copy(encoded[headerSize:], frame.payload)
	return encoded
}

func decodeMux(encoded []byte) (muxFrame, error) {
	var frame muxFrame
	if len(encoded) < headerSize || len(encoded) > headerSize+MaxData || encoded[0] != 2 || binary.BigEndian.Uint32(encoded[6:10]) != uint32(len(encoded)-headerSize) {
		return frame, ErrProtocol
	}
	frame = muxFrame{encoded[1], binary.BigEndian.Uint32(encoded[2:6]), encoded[headerSize:]}
	if frame.kind >= muxDNSQuery && frame.kind <= muxDNSCancel {
		if frame.id != 0 || len(frame.payload) < 4 || binary.BigEndian.Uint32(frame.payload) == 0 || binary.BigEndian.Uint32(frame.payload) > muxMaxID {
			return frame, ErrProtocol
		}
		size := len(frame.payload) - 4
		if (frame.kind == muxDNSQuery || frame.kind == muxDNSResponse) && (size < 12 || size > MuxMaxDNSMessage) || (frame.kind == muxDNSError || frame.kind == muxDNSCancel) && size != 0 {
			return frame, ErrProtocol
		}
		return frame, nil
	}
	if frame.id == 0 || frame.id > muxMaxID || frame.id%2 == 0 {
		return frame, ErrProtocol
	}
	switch frame.kind {
	case openFrame, openError:
		if len(frame.payload) == 0 || len(frame.payload) > 512 {
			return frame, ErrProtocol
		}
	case dataFrame:
		if len(frame.payload) == 0 {
			return frame, ErrProtocol
		}
	case muxWindowUpdate:
		if len(frame.payload) != 4 || binary.BigEndian.Uint32(frame.payload) == 0 || binary.BigEndian.Uint32(frame.payload) > MuxWindow {
			return frame, ErrProtocol
		}
	case openOK, finFrame, resetFrame, closeFrame:
		if len(frame.payload) != 0 {
			return frame, ErrProtocol
		}
	default:
		return frame, ErrProtocol
	}
	return frame, nil
}
