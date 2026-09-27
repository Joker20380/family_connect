package reliablestream

import (
	"encoding/binary"
	"errors"
	"time"
)

const HeaderSize = 64
const MaxPayload = 32768
const MaxWindow = 32

const (
	openFrame byte = 1 + iota
	dataFrame
	ackFrame
	resetFrame
)

var ErrProtocol = errors.New("reliable stream: protocol violation")
var ErrExhausted = errors.New("reliable stream: recovery exhausted")
var ErrReset = errors.New("reliable stream: remote reset")
var ErrClosed = errors.New("reliable stream: closed")

type Config struct {
	Payload       int
	SendWindow    int
	ReceiveWindow int
	RTO           time.Duration
	MaxRetries    int
	MaxAge        time.Duration
}

func DefaultConfig() Config {
	return Config{Payload: 16384, SendWindow: 8, ReceiveWindow: 16, RTO: time.Second, MaxRetries: 8, MaxAge: 20 * time.Second}
}

func (config Config) validate() error {
	if config.Payload < 1 || config.Payload > MaxPayload || config.SendWindow < 1 || config.SendWindow > MaxWindow || config.ReceiveWindow < 1 || config.ReceiveWindow > MaxWindow || config.RTO < 10*time.Millisecond || config.RTO > 10*time.Second || config.MaxRetries < 1 || config.MaxRetries > 32 || config.MaxAge < config.RTO || config.MaxAge > time.Minute {
		return ErrProtocol
	}
	return nil
}

type epoch [16]byte

type frame struct {
	kind    byte
	source  epoch
	target  epoch
	seq     uint64
	ack     uint64
	bits    uint32
	window  int
	payload int
	data    []byte
}

func encode(packet frame) []byte {
	raw := make([]byte, HeaderSize+len(packet.data))
	copy(raw, "FRS1")
	raw[4] = packet.kind
	binary.BigEndian.PutUint16(raw[6:], uint16(len(packet.data)))
	copy(raw[8:24], packet.source[:])
	copy(raw[24:40], packet.target[:])
	binary.BigEndian.PutUint64(raw[40:], packet.seq)
	binary.BigEndian.PutUint64(raw[48:], packet.ack)
	binary.BigEndian.PutUint32(raw[56:], packet.bits)
	binary.BigEndian.PutUint16(raw[60:], uint16(packet.window))
	binary.BigEndian.PutUint16(raw[62:], uint16(packet.payload))
	copy(raw[HeaderSize:], packet.data)
	return raw
}

func decode(raw []byte) (frame, error) {
	var packet frame
	if len(raw) < HeaderSize || len(raw) > HeaderSize+MaxPayload || string(raw[:4]) != "FRS1" || raw[5] != 0 || int(binary.BigEndian.Uint16(raw[6:])) != len(raw)-HeaderSize {
		return packet, ErrProtocol
	}
	packet.kind = raw[4]
	copy(packet.source[:], raw[8:24])
	copy(packet.target[:], raw[24:40])
	packet.seq = binary.BigEndian.Uint64(raw[40:])
	packet.ack = binary.BigEndian.Uint64(raw[48:])
	packet.bits = binary.BigEndian.Uint32(raw[56:])
	packet.window = int(binary.BigEndian.Uint16(raw[60:]))
	packet.payload = int(binary.BigEndian.Uint16(raw[62:]))
	packet.data = raw[HeaderSize:]
	if packet.source == (epoch{}) || packet.kind < openFrame || packet.kind > resetFrame {
		return frame{}, ErrProtocol
	}
	if packet.kind == dataFrame {
		if len(packet.data) == 0 || packet.ack != 0 || packet.bits != 0 {
			return frame{}, ErrProtocol
		}
	} else if len(packet.data) != 0 || packet.seq != 0 || (packet.kind != ackFrame && (packet.ack != 0 || packet.bits != 0)) {
		return frame{}, ErrProtocol
	}
	if packet.kind == openFrame {
		if packet.window < 1 || packet.window > MaxWindow || packet.payload < 1 || packet.payload > MaxPayload {
			return frame{}, ErrProtocol
		}
	} else if packet.target == (epoch{}) || packet.window != 0 || packet.payload != 0 {
		return frame{}, ErrProtocol
	}
	return packet, nil
}
