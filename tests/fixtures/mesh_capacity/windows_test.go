package reliablestream

import (
	"bytes"
	"context"
	"fmt"
	"testing"
	"time"
)

func TestCapacityWindows(test *testing.T) {
	for _, windows := range [][2]int{{8, 16}, {8, 32}, {16, 32}, {32, 32}} {
		test.Run(fmt.Sprint(windows), func(test *testing.T) {
			config := DefaultConfig()
			config.SendWindow, config.ReceiveWindow = windows[0], windows[1]
			for name, injection := range map[string]faults{"clean": {}, "head_late": {drop: map[uint64]int{0: 4}}, "loss_reorder_dup_ack": {drop: map[uint64]int{0: 2, 31: 1}, reorder: true, duplicate: true, ackLoss: 10}, "tail_bitmap": {drop: map[uint64]int{0: 1, 31: 1}, delay: 140}} {
				test.Run(name, func(test *testing.T) { capacitySimulate(test, injection, config) })
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			leftEndpoint, rightEndpoint := endpoints()
			left, err := New(ctx, leftEndpoint, config)
			if err != nil {
				test.Fatal(err)
			}
			defer left.Close()
			right, err := New(ctx, rightEndpoint, config)
			if err != nil {
				test.Fatal(err)
			}
			defer right.Close()
			for index := 0; index < config.SendWindow; index++ {
				if err := left.SendContext(ctx, []byte{byte(index)}); err != nil {
					test.Fatal(err)
				}
			}
			blocked := make(chan error, 1)
			go func() { blocked <- left.SendContext(ctx, []byte{99}) }()
			select {
			case <-blocked:
				test.Fatal("window did not block")
			case <-time.After(80 * time.Millisecond):
			}
			for index := 0; index < config.SendWindow; index++ {
				data, err := right.Recv(ctx)
				if err != nil || !bytes.Equal(data, []byte{byte(index)}) {
					test.Fatal("slow consumer", err)
				}
			}
			if err := <-blocked; err != nil {
				test.Fatal(err)
			}
			if left.Stats().Performance.EffectiveWindow != config.SendWindow {
				test.Fatal("effective window")
			}
			left.Close()
			right.Close()
			if left.Stats().BufferedBytes != 0 || right.Stats().BufferedBytes != 0 {
				test.Fatal("close retained memory")
			}
		})
	}
}
