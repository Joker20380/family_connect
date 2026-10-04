package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

type framedReliableEndpoint struct {
	peer       *framedReliableEndpoint
	incoming   chan []byte
	done       chan struct{}
	once       sync.Once
	sendMu     sync.Mutex
	receiveMu  sync.Mutex
	assembler  *reassembler
	reorder    *reorderBuffer
	frame      vp8FrameState
	sender     uint32
	message    uint32
	sequence   uint16
	timestamp  uint32
	dropUntil  int
	attempts   int
	droppedRTP int
}

func framedReliablePair() (*framedReliableEndpoint, *framedReliableEndpoint) {
	points := make([]*framedReliableEndpoint, 2)
	for index := range points {
		point := &framedReliableEndpoint{incoming: make(chan []byte, 64), done: make(chan struct{}), sender: uint32(index + 1), sequence: 65530, reorder: newReorderBuffer()}
		point.assembler = newReassembler(point.sender, func(data []byte) {
			select {
			case point.incoming <- data:
			case <-point.done:
			}
		})
		points[index] = point
	}
	points[0].peer, points[1].peer = points[1], points[0]
	return points[0], points[1]
}

func (point *framedReliableEndpoint) SendContext(ctx context.Context, data []byte) error {
	point.sendMu.Lock()
	defer point.sendMu.Unlock()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-point.done:
		return reliablestream.ErrClosed
	default:
	}
	missingHead := len(data) >= reliablestream.HeaderSize && string(data[:4]) == "FRS1" && data[4] == 2 && binary.BigEndian.Uint64(data[40:]) == 0
	if missingHead {
		point.attempts++
	}
	point.message++
	fragments, err := encodeFragments(point.sender, point.message, data)
	if err != nil {
		return err
	}
	payloader := &codecs.VP8Payloader{}
	point.peer.receiveMu.Lock()
	defer point.peer.receiveMu.Unlock()
	for fragmentIndex, fragment := range fragments {
		point.timestamp += 3000
		packets := payloader.Payload(1100, encodeVP8DataFrame(fragment))
		for packetIndex, payload := range packets {
			packet := &rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: point.sequence, Timestamp: point.timestamp, Marker: packetIndex == len(packets)-1}, Payload: payload}
			point.sequence++
			if missingHead && point.attempts <= point.dropUntil && fragmentIndex == 0 && packetIndex == 2 {
				point.droppedRTP++
				continue
			}
			point.peer.reorder.push(packet, func(ordered *rtp.Packet) {
				frame := point.peer.frame.process(ordered)
				if frame == nil {
					return
				}
				if fragment, valid := decodeVP8Frame(frame); valid {
					point.peer.assembler.ingest(fragment)
				}
			})
		}
	}
	return nil
}

func (point *framedReliableEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case data := <-point.incoming:
		return data, nil
	case <-point.done:
		return nil, reliablestream.ErrClosed
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (point *framedReliableEndpoint) Close() error {
	point.once.Do(func() { close(point.done) })
	return nil
}

func TestReliableStreamOverVP8MissingRTPWithFreshACK(test *testing.T) {
	for _, scenario := range []struct {
		name      string
		dropUntil int
		exhausted bool
	}{{"no_loss", 0, false}, {"healed_gap", 4, false}, {"persistent_gap", 100, true}} {
		test.Run(scenario.name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			recorder := sessiontrace.New(strings.Repeat("1", 64), nil)
			leftEndpoint, rightEndpoint := framedReliablePair()
			leftEndpoint.dropUntil = scenario.dropUntil
			config := reliablestream.DefaultConfig()
			left, err := reliablestream.New(sessiontrace.With(ctx, recorder), leftEndpoint, config)
			if err != nil {
				test.Fatal(err)
			}
			defer left.Close()
			right, err := reliablestream.New(ctx, rightEndpoint, config)
			if err != nil {
				test.Fatal(err)
			}
			defer right.Close()
			for index := 0; index < config.SendWindow; index++ {
				if err := left.SendContext(ctx, bytes.Repeat([]byte{byte(index + 1)}, config.Payload)); err != nil {
					test.Fatal(err)
				}
			}
			if scenario.exhausted {
				if err := left.SendContext(ctx, []byte("window-must-remain-full")); !errors.Is(err, reliablestream.ErrExhausted) {
					test.Fatal("expected genuine stream exhaustion", err)
				}
				failure := recorder.Snapshot().FirstFailure
				if failure == nil || failure.Reason != "RELIABLE_RETRY_EXHAUSTED" || failure.ReliableRetries != 8 || failure.ReliablePending != 8 || failure.ReliableSacked != 0 || failure.ReliableACKReceived == 0 || failure.ReliableProgressAgeMS < 8000 || failure.ReliableACKAgeMS > uint64(2*config.RTO/time.Millisecond) {
					test.Fatal("missing fresh ACK/no-progress evidence", failure)
				}
				if left.Stats().Terminal != "recovery_exhausted" || left.Stats().SACKReceived == 0 {
					test.Fatal("wrong terminal or no later-block SACK")
				}
				flow := left.Stats().Flow
				leftEndpoint.peer.receiveMu.Lock()
				assembly := leftEndpoint.peer.assembler.delivery()
				leftEndpoint.peer.receiveMu.Unlock()
				if flow.SendBase != 0 || flow.SendNext != 8 || flow.Pending != 8 || flow.HeadRetries != 8 || flow.ACKBase != 0 || flow.ACKMask&254 != 254 || failure.Delivery.Flow.Pending != 8 || assembly.Pending == nil || assembly.Pending.Mask&1 != 0 || assembly.Pending.DataKnown {
					test.Fatal("cross-layer retained hole evidence missing", flow, assembly)
				}
			} else {
				for index := 0; index < config.SendWindow; index++ {
					data, err := right.Recv(ctx)
					if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(index + 1)}, config.Payload)) {
						test.Fatal("ordered byte-exact delivery failed", index, err)
					}
				}
				if err := left.SendContext(ctx, []byte("window-reopened")); err != nil {
					test.Fatal(err)
				}
				data, err := right.Recv(ctx)
				if err != nil || string(data) != "window-reopened" || recorder.Snapshot().FirstFailure != nil {
					test.Fatal("healed framing gap did not restore progress", err)
				}
			}
			leftEndpoint.sendMu.Lock()
			attempts, dropped := leftEndpoint.attempts, leftEndpoint.droppedRTP
			leftEndpoint.sendMu.Unlock()
			expected := min(scenario.dropUntil, config.MaxRetries+1)
			if dropped != expected || scenario.exhausted && attempts != config.MaxRetries+1 {
				test.Fatalf("wrong actual RTP loss: attempts=%d dropped=%d", attempts, dropped)
			}
			test.Logf("head DATA attempts=%d dropped RTP=%d ACKs=%d SACKs=%d", attempts, dropped, left.Stats().ACKReceived, left.Stats().SACKReceived)
		})
	}
}
