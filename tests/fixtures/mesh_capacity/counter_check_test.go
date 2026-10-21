package main

import (
	"context"
	"testing"
	"time"
)

type capacityCounterSink struct{ buffer []byte }

func (sink *capacityCounterSink) SendContext(_ context.Context, data []byte) error {
	sink.buffer = append(sink.buffer[:0], data...)
	return nil
}
func (sink *capacityCounterSink) Recv(context.Context) ([]byte, error) { return sink.buffer, nil }
func (*capacityCounterSink) Close() error                              { return nil }

func TestCapacityReadVerifyCounters(test *testing.T) {
	sink := &capacityCounterSink{}
	endpoint := &capacityEndpoint{PacketEndpoint: sink, Messages: map[int]uint64{}, Data: map[int]uint64{}, Records: map[int]uint64{}}
	template, buffer := capacityTemplate(21), make([]byte, 65536)
	started := time.Now()
	for index := 0; index < 32768; index++ {
		packet := capacityPacket(buffer, template, 21, index, 16448, 3)
		if err := endpoint.SendContext(context.Background(), packet); err != nil {
			test.Fatal(err)
		}
		received, err := endpoint.Recv(context.Background())
		if err != nil || !capacityValid(received, template, 21) {
			test.Fatal("read/verify", err)
		}
	}
	if endpoint.Messages[16448] != 32768 {
		test.Fatal("counter mismatch")
	}
	test.Logf("generation/copy/read/full_verify/counters %.2f Mbit/s in %.4fs; local-only", float64(32768*16448*8)/time.Since(started).Seconds()/1e6, time.Since(started).Seconds())
}
