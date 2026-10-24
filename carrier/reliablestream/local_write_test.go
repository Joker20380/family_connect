package reliablestream

import (
	"bytes"
	"context"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/localwrite"
)

type localEndpoint struct {
	*testEndpoint
	mu       sync.Mutex
	attempts map[uint64]int
	retry    chan *localwrite.Write
}

func (endpoint *localEndpoint) SendContext(ctx context.Context, data []byte) error {
	packet, err := decode(data)
	if err != nil || packet.kind != dataFrame {
		return endpoint.testEndpoint.SendContext(ctx, data)
	}
	endpoint.mu.Lock()
	endpoint.attempts[packet.seq]++
	attempt := endpoint.attempts[packet.seq]
	endpoint.mu.Unlock()
	write, err := localwrite.Register(ctx, 1)
	if err != nil {
		return err
	}
	if packet.seq == 0 && attempt == 2 {
		endpoint.retry <- write
		return nil
	}
	if write.Begin() {
		err = endpoint.testEndpoint.SendContext(ctx, data)
		write.Complete(err)
	}
	return err
}

func TestACKReleasesWhileRetryWaitsForLocalWrite(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	ctx = localwrite.WithCompletion(ctx)
	left, right := endpoints()
	point := &localEndpoint{testEndpoint: left, attempts: make(map[uint64]int), retry: make(chan *localwrite.Write, 1)}
	var mutex sync.Mutex
	var held []byte
	hold := true
	right.drop = func(raw []byte) bool {
		packet, _ := decode(raw)
		mutex.Lock()
		defer mutex.Unlock()
		if packet.kind == ackFrame && hold {
			if packet.ack > 0 {
				held = bytes.Clone(raw)
			}
			return true
		}
		return false
	}
	config := DefaultConfig()
	config.RTO = 30 * time.Millisecond
	config.MaxAge = time.Second
	sender, err := New(ctx, point, config)
	if err != nil {
		test.Fatal(err)
	}
	defer sender.Close()
	receiver, err := New(ctx, right, config)
	if err != nil {
		test.Fatal(err)
	}
	defer receiver.Close()
	if err = sender.SendContext(ctx, []byte("first")); err != nil {
		test.Fatal(err)
	}
	if data, err := receiver.Recv(ctx); err != nil || string(data) != "first" {
		test.Fatal("first delivery", err)
	}
	var queued *localwrite.Write
	select {
	case queued = <-point.retry:
	case <-ctx.Done():
		test.Fatal("no real sent-DATA retry")
	}
	mutex.Lock()
	ack := bytes.Clone(held)
	hold = false
	mutex.Unlock()
	if len(ack) == 0 {
		test.Fatal("no actual cumulative ACK")
	}
	left.in <- ack
	deadline := time.Now().Add(200 * time.Millisecond)
	for sender.Stats().Flow.SendBase != 1 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if sender.Stats().Flow.SendBase != 1 {
		test.Fatal("ACK blocked by local writer")
	}
	if queued.Begin() {
		test.Fatal("ACKed queued retry still starts")
	}
	for index := 0; index < 12; index++ {
		payload := bytes.Repeat([]byte{byte(index + 1)}, config.Payload)
		if err = sender.SendContext(ctx, payload); err != nil {
			test.Fatal(err)
		}
		data, err := receiver.Recv(ctx)
		if err != nil || !bytes.Equal(data, payload) {
			test.Fatal("subsequent byte-exact delivery", err)
		}
	}
	if sender.Stats().Retransmissions != 1 {
		test.Fatal("unexpected retry copies", sender.Stats().Retransmissions)
	}
}
