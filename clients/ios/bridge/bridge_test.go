package bridge

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"gvisor.dev/gvisor/pkg/buffer"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

func dnsPacket() []byte {
	data := make([]byte, 40)
	copy(data, []byte{0x45, 0, 0, 40, 0, 1, 0, 0, 64, 17})
	copy(data[12:20], []byte{198, 18, 0, 2, 198, 18, 0, 1})
	copy(data[20:], []byte{0xc0, 0, 0, 53, 0, 20, 0, 0, 0x12, 0x34})
	var checksum uint32
	for offset := 0; offset < 20; offset += 2 {
		checksum += uint32(binary.BigEndian.Uint16(data[offset:]))
	}
	for checksum > 0xffff {
		checksum = checksum&0xffff + checksum>>16
	}
	binary.BigEndian.PutUint16(data[10:], ^uint16(checksum))
	return data
}

func waitState(test *testing.T, bridge *Bridge, expected int) {
	test.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		state, _ := bridge.Status()
		if state == expected {
			return
		}
		time.Sleep(time.Millisecond)
	}
	state, failure := bridge.Status()
	test.Fatalf("state %d failure %d, wanted %d", state, failure, expected)
}

func TestPacketCopyDNSAndProtocolFamily(test *testing.T) {
	gate := make(chan struct{})
	fixture := NewFixture()
	bridge := New(func(ctx context.Context) (*wholedevice.Session, error) {
		select {
		case <-gate:
			return fixture.Attach(ctx)
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	})
	defer bridge.Stop()
	input := dnsPacket()
	original := append([]byte(nil), input...)
	if bridge.Write(input, 4) != OK {
		test.Fatal("write")
	}
	clear(input)
	close(gate)
	waitState(test, bridge, Ready)
	output, family, code := bridge.Read(time.Second)
	if code != OK || family != 4 || len(output) != 40 {
		test.Fatalf("read: %d %d %d", code, family, len(output))
	}
	if !bytes.Equal(output[12:16], original[16:20]) || !bytes.Equal(output[16:20], original[12:16]) || !bytes.Equal(output[28:30], original[28:30]) || output[30]&0x80 == 0 {
		test.Fatal("packet conversion/copy/response")
	}
	if bridge.Write(original, 6) != Invalid {
		test.Fatal("mismatched family")
	}
	ipv6 := make([]byte, 40)
	ipv6[0] = 0x60
	if bridge.Write(ipv6, 6) != Unsupported {
		test.Fatal("IPv6 must not bypass")
	}
	original[23] = 54
	if bridge.Write(original, 4) != OK {
		test.Fatal("input")
	}
	if _, _, code := bridge.Read(30 * time.Millisecond); code != Timeout {
		test.Fatal("unsupported UDP escaped", code)
	}
	if bridge.Write(make([]byte, MTU+1), 4) != Invalid || bridge.Write([]byte{0x45}, 4) != Invalid {
		test.Fatal("bounds")
	}
}

func TestBoundedIngressAndCancelStartup(test *testing.T) {
	bridge := New(func(ctx context.Context) (*wholedevice.Session, error) { <-ctx.Done(); return nil, ctx.Err() })
	for index := 0; index < QueueSize; index++ {
		if bridge.Write(dnsPacket(), 4) != OK {
			test.Fatal(index)
		}
	}
	if bridge.Write(dnsPacket(), 4) != Full {
		test.Fatal("unbounded ingress")
	}
	bridge.Stop()
	bridge.Stop()
	if state, failure := bridge.Status(); state != Stopped || failure != 0 {
		test.Fatal(state, failure)
	}
	if len(bridge.incoming) != 0 || bridge.endpoint.NumQueued() != 0 || bridge.Write(dnsPacket(), 4) != Closed {
		test.Fatal("cleanup")
	}
}

func TestBoundedEndpointAndRelease(test *testing.T) {
	bridge := New(NewFixture().Attach)
	defer bridge.Stop()
	waitState(test, bridge, Ready)
	for index := 0; index <= QueueSize; index++ {
		packet := stack.NewPacketBuffer(stack.PacketBufferOptions{Payload: buffer.MakeWithData(dnsPacket())})
		var packets stack.PacketBufferList
		packets.PushBack(packet)
		count, err := bridge.endpoint.WritePackets(packets)
		packet.DecRef()
		if index < QueueSize && (count != 1 || err != nil) {
			test.Fatal("early output drop")
		}
		if index == QueueSize && (count != 0 || err != nil) {
			test.Fatal("unbounded output")
		}
	}
	if bridge.endpoint.NumQueued() != QueueSize {
		test.Fatal("queue size")
	}
	bridge.Stop()
	if bridge.endpoint.NumQueued() != 0 {
		test.Fatal("leaked output refs")
	}
}

func TestFailureIsRetained(test *testing.T) {
	for _, startupError := range []error{errors.New("synthetic failure"), ErrUnderlay} {
		bridge := New(func(context.Context) (*wholedevice.Session, error) { return nil, startupError })
		waitState(test, bridge, Failed)
		expected := StartupFailed
		if startupError == ErrUnderlay {
			expected = UnderlayDenied
		}
		bridge.Stop()
		if state, failure := bridge.Status(); state != Failed || failure != expected {
			test.Fatal(state, failure)
		}
		if _, _, code := bridge.Read(time.Second); code != expected {
			test.Fatal("lost error", code)
		}
	}
}

func TestTransportFailureAndRecreate(test *testing.T) {
	for cycle := 0; cycle < 20; cycle++ {
		fixture := NewFixture()
		bridge := New(fixture.Attach)
		waitState(test, bridge, Ready)
		fixture.Close()
		waitState(test, bridge, Failed)
		bridge.Stop()
		if state, failure := bridge.Status(); state != Failed || failure != TransportFailed {
			test.Fatal(state, failure)
		}
	}
}

func TestCancelReadAndConcurrentStop(test *testing.T) {
	bridge := New(NewFixture().Attach)
	waitState(test, bridge, Ready)
	result := make(chan int, 1)
	go func() { _, _, code := bridge.Read(time.Second); result <- code }()
	var workers sync.WaitGroup
	for index := 0; index < 8; index++ {
		workers.Add(1)
		go func() { defer workers.Done(); bridge.Write(dnsPacket(), 4); bridge.Stop() }()
	}
	workers.Wait()
	select {
	case code := <-result:
		if code != Closed && code != OK {
			test.Fatal(code)
		}
	case <-time.After(time.Second):
		test.Fatal("reader stranded")
	}
}

func TestUnderlayRejectsNonPhysicalInterface(test *testing.T) {
	for _, name := range []string{"", "lo0", "utun0", "en999999999"} {
		if protect, err := boundInterface(name); err == nil || protect != nil {
			test.Fatal("unsafe interface accepted")
		}
	}
}
