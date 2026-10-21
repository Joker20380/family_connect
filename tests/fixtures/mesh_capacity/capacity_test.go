package main

import (
	"testing"
	"time"
)

func TestCapacityPayload(test *testing.T) {
	template, buffer := capacityTemplate(21), make([]byte, 65536)
	for _, size := range []int{64, 128, 1024, 16320, 16384, 16448} {
		packet := capacityPacket(buffer, template, 21, 37, size, 3)
		if !capacityValid(packet, template, 21) {
			test.Fatal(size)
		}
		packet[size-1] ^= 1
		if capacityValid(packet, template, 21) {
			test.Fatal("corruption accepted")
		}
	}
	started := time.Now()
	for index := 0; index < 32768; index++ {
		packet := capacityPacket(buffer, template, 21, index, 16448, 3)
		if !capacityValid(packet, template, 21) {
			test.Fatal(index)
		}
	}
	test.Logf("generate+verify %.2f Mbit/s; preallocated, 512MiB local-only, %.4fs", float64(32768*16448*8)/time.Since(started).Seconds()/1e6, time.Since(started).Seconds())
}
