package familysession

import (
	"bytes"
	"context"
	"fmt"
	"testing"
	"time"
)

type delayedFrame struct {
	payload []byte
	ready   time.Time
}
type latencyEndpoint struct {
	PacketEndpoint
	ctx   context.Context
	queue chan delayedFrame
}

func latencyLink(ctx context.Context, point PacketEndpoint) *latencyEndpoint {
	link := &latencyEndpoint{PacketEndpoint: point, ctx: ctx, queue: make(chan delayedFrame, 64)}
	go func() {
		for {
			select {
			case frame := <-link.queue:
				timer := time.NewTimer(time.Until(frame.ready))
				select {
				case <-timer.C:
				case <-ctx.Done():
					timer.Stop()
					return
				}
				if point.SendContext(ctx, frame.payload) != nil {
					return
				}
			case <-ctx.Done():
				return
			}
		}
	}()
	return link
}
func (link *latencyEndpoint) SendContext(ctx context.Context, payload []byte) error {
	select {
	case link.queue <- delayedFrame{bytes.Clone(payload), time.Now().Add(40 * time.Millisecond)}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-link.ctx.Done():
		return link.ctx.Err()
	}
}

func TestQueuedMessageEnvelope(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	clientProfile, serverProfile := profiles(test)
	left, right := pair()
	type result struct {
		session *Session
		err     error
	}
	serverReady := make(chan result, 1)
	go func() {
		session, err := Open(ctx, latencyLink(ctx, right), encoded(serverProfile), true)
		serverReady <- result{session, err}
	}()
	client, err := Open(ctx, latencyLink(ctx, left), encoded(clientProfile), false)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	opened := <-serverReady
	if opened.err != nil {
		test.Fatal(opened.err)
	}
	defer opened.session.Close()
	received := make(chan error, 1)
	const count = 256
	go func() {
		for index := 0; index < count; index++ {
			payload, err := opened.session.Recv(ctx)
			if err != nil {
				received <- err
				return
			}
			expected := bytes.Repeat([]byte{byte(index)}, 384)
			if !bytes.Equal(payload, expected) {
				received <- fmt.Errorf("body mismatch %d", index)
				return
			}
		}
		received <- nil
	}()
	before := client.ReliabilityStats().DataSent
	start := time.Now()
	batched, ok := any(client).(interface {
		SendBatchContext(context.Context, [][]byte) error
	})
	for offset := 0; offset < count; offset += 16 {
		var group [][]byte
		for index := offset; index < offset+16; index++ {
			group = append(group, bytes.Repeat([]byte{byte(index)}, 384))
		}
		if ok {
			err = batched.SendBatchContext(ctx, group)
		} else {
			for _, payload := range group {
				if err = client.SendContext(ctx, payload); err != nil {
					break
				}
			}
		}
		if err != nil {
			test.Fatal(err)
		}
	}
	if err := <-received; err != nil {
		test.Fatal(err)
	}
	frames := client.ReliabilityStats().DataSent - before
	test.Logf("ENVELOPE batched=%v bytes=%d messages=%d data_frames=%d elapsed_ms=%d model=40ms_each_way_no_loss", ok, count*384, count, frames, time.Since(start).Milliseconds())
	if ok && frames >= count/2 {
		test.Fatalf("batch failed to reduce data frames: %d", frames)
	}
}
