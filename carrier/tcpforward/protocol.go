package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

const MaxData = 16 << 10
const ForwarderBufferBound = 3*MaxData + 2*headerSize
const streamID = 1
const headerSize = 10

const (
	openFrame byte = iota + 1
	openOK
	openError
	dataFrame
	finFrame
	resetFrame
	closeFrame
)

var ErrProtocol = errors.New("TCP forwarding protocol error")
var ErrReset = errors.New("TCP forwarding reset")

type OpenRequest struct {
	Host      string `json:"host"`
	Port      int    `json:"port"`
	TimeoutMS int    `json:"timeout_ms,omitempty"`
}

type OpenError struct {
	Code string `json:"code"`
}

func (failure *OpenError) Error() string { return "TCP OPEN: " + failure.Code }

type Stats struct {
	OpenRequests      uint64  `json:"open_requests"`
	OpenOK            uint64  `json:"open_ok"`
	OpenErrors        uint64  `json:"open_errors"`
	ConnectMS         float64 `json:"connect_ms"`
	ToTarget          uint64  `json:"to_target_bytes"`
	FromTarget        uint64  `json:"from_target_bytes"`
	DataSent          uint64  `json:"data_sent"`
	DataReceived      uint64  `json:"data_received"`
	TCPReads          uint64  `json:"tcp_reads"`
	TCPWrites         uint64  `json:"tcp_writes"`
	PartialWrites     uint64  `json:"partial_writes"`
	LocalFIN          uint64  `json:"local_fin"`
	RemoteFIN         uint64  `json:"remote_fin"`
	EOFs              uint64  `json:"eofs"`
	Resets            uint64  `json:"resets"`
	RetainedHighWater int     `json:"retained_high_water"`
	RetainedBytes     int     `json:"retained_bytes"`
	BufferBoundBytes  int     `json:"buffer_bound_bytes"`
	ActiveSockets     int     `json:"active_sockets"`
	CloseReason       string  `json:"close_reason"`
}

type Metrics struct {
	mu    sync.Mutex
	stats Stats
}

func (metrics *Metrics) Snapshot() Stats {
	metrics.mu.Lock()
	defer metrics.mu.Unlock()
	return metrics.stats
}
func (metrics *Metrics) update(change func(*Stats)) {
	metrics.mu.Lock()
	defer metrics.mu.Unlock()
	change(&metrics.stats)
}

func (metrics *Metrics) retain(size int) {
	metrics.update(func(stats *Stats) {
		stats.RetainedBytes += size
		stats.RetainedHighWater = max(stats.RetainedHighWater, stats.RetainedBytes)
		stats.BufferBoundBytes = ForwarderBufferBound
	})
}

func encode(kind byte, payload []byte) []byte {
	frame := make([]byte, headerSize+len(payload))
	frame[0], frame[1] = 1, kind
	binary.BigEndian.PutUint32(frame[2:6], streamID)
	binary.BigEndian.PutUint32(frame[6:10], uint32(len(payload)))
	copy(frame[headerSize:], payload)
	return frame
}

func decode(frame []byte) (byte, []byte, error) {
	if len(frame) < headerSize || len(frame) > headerSize+MaxData || frame[0] != 1 || binary.BigEndian.Uint32(frame[2:6]) != streamID || int(binary.BigEndian.Uint32(frame[6:10])) != len(frame)-headerSize {
		return 0, nil, ErrProtocol
	}
	kind, payload := frame[1], frame[headerSize:]
	switch kind {
	case openFrame, openError:
		if len(payload) == 0 || len(payload) > 512 {
			return 0, nil, ErrProtocol
		}
	case dataFrame:
		if len(payload) == 0 {
			return 0, nil, ErrProtocol
		}
	case openOK, finFrame, resetFrame, closeFrame:
		if len(payload) != 0 {
			return 0, nil, ErrProtocol
		}
	default:
		return 0, nil, ErrProtocol
	}
	return kind, payload, nil
}

func decodeJSON(payload []byte, value any) error {
	decoder := json.NewDecoder(bytes.NewReader(payload))
	decoder.DisallowUnknownFields()
	if decoder.Decode(value) != nil || decoder.Decode(new(any)) != io.EOF {
		return ErrProtocol
	}
	return nil
}

func receive(ctx context.Context, endpoint familysession.PacketEndpoint) (byte, []byte, error) {
	payload, err := endpoint.Recv(ctx)
	if err != nil {
		return 0, nil, err
	}
	return decode(payload)
}

func boundedControl(endpoint familysession.PacketEndpoint, kind byte) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	stop := context.AfterFunc(ctx, func() { endpoint.Close() })
	defer stop()
	return endpoint.SendContext(ctx, encode(kind, nil))
}
