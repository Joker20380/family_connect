package main

import (
	"bytes"
	"encoding/binary"
	"net"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/amnezia-vpn/amneziawg-go/v3/tun"
)

type testTun struct {
	closed  chan struct{}
	once    sync.Once
	written chan []byte
}

func (device *testTun) File() *os.File           { return nil }
func (device *testTun) Name() (string, error)    { return "synthetic", nil }
func (device *testTun) MTU() (int, error)        { return 1280, nil }
func (device *testTun) Events() <-chan tun.Event { return nil }
func (device *testTun) BatchSize() int           { return 1 }
func (device *testTun) Read(_ [][]byte, _ []int, _ int) (int, error) {
	<-device.closed
	return 0, net.ErrClosed
}
func (device *testTun) Write(packets [][]byte, offset int) (int, error) {
	for _, packet := range packets {
		device.written <- bytes.Clone(packet[offset:])
	}
	return len(packets), nil
}
func (device *testTun) Close() error { device.once.Do(func() { close(device.closed) }); return nil }
func fixtureTun() (*healthTun, *testTun) {
	device := &testTun{closed: make(chan struct{}), written: make(chan []byte, 8)}
	return newHealthTun(device), device
}
func question() []byte {
	return []byte{12, 34, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 'x', 7, 'e', 'x', 'a', 'm', 'p', 'l', 'e', 3, 'c', 'o', 'm', 0, 0, 1, 0, 1}
}
func TestHealthPacketAndStrictDemultiplex(test *testing.T) {
	owner, device := fixtureTun()
	defer owner.Close()
	query := question()
	answer := make(chan []byte, 1)
	go func() { answer <- owner.query("10.78.0.4", query, time.Second) }()
	packet := make([]byte, 1280)
	sizes := make([]int, 1)
	if count, err := owner.Read([][]byte{packet}, sizes, 0); err != nil || count != 1 {
		test.Fatal("injected query", err)
	}
	packet = packet[:sizes[0]]
	if checksum(packet[:20]) != 0 || !bytes.Equal(packet[28:], query) || binary.BigEndian.Uint16(packet[22:24]) != 53 {
		test.Fatal("invalid packet")
	}
	reply := bytes.Clone(packet)
	copy(reply[12:16], packet[16:20])
	copy(reply[16:20], packet[12:16])
	copy(reply[20:22], packet[22:24])
	copy(reply[22:24], packet[20:22])
	reply[30] = 0x81
	reply[31] = 0x80
	foreign := bytes.Clone(reply)
	foreign[28] ^= 1
	if count, err := owner.Write([][]byte{foreign}, 0); err != nil || count != 1 {
		test.Fatal("ordinary packet write")
	}
	if !bytes.Equal(<-device.written, foreign) {
		test.Fatal("unrelated packet modified")
	}
	if count, err := owner.Write([][]byte{reply}, 0); err != nil || count != 1 {
		test.Fatal("probe response write")
	}
	select {
	case received := <-answer:
		if !bytes.Equal(received, reply[28:]) {
			test.Fatal("response mismatch")
		}
	case <-time.After(2 * time.Second):
		test.Fatal("probe stalled")
	}
	if len(device.written) != 0 {
		test.Fatal("probe leaked into kernel")
	}
}
func TestHealthDeadlineCloseAndInputBounds(test *testing.T) {
	owner, _ := fixtureTun()
	defer owner.Close()
	for _, source := range []string{"::1", "not-an-ip"} {
		if owner.query(source, question(), time.Millisecond) != nil {
			test.Fatal("invalid address")
		}
	}
	if owner.query("10.78.0.4", question(), 3*time.Second) != nil {
		test.Fatal("unbounded deadline")
	}
	began := time.Now()
	if owner.query("10.78.0.4", question(), 20*time.Millisecond) != nil {
		test.Fatal("fabricated reply")
	}
	if time.Since(began) > time.Second {
		test.Fatal("timeout not bounded")
	}
	answer := make(chan []byte, 1)
	go func() { answer <- owner.query("10.78.0.4", question(), time.Second) }()
	owner.Close()
	select {
	case received := <-answer:
		if received != nil {
			test.Fatal("closed reply")
		}
	case <-time.After(time.Second):
		test.Fatal("close stalled")
	}
}
