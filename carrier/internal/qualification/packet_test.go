package qualification

import (
	"bytes"
	"context"
	"encoding/binary"
	"net"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestRoomLifecycleAndIndependentEndpoints(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	done := make(chan error, 1)
	go func() { done <- Relay(ctx, listener) }()
	defer func() { cancel(); <-done }()
	provider := Provider{Address: listener.Addr().String()}
	if _, err := provider.Connect(ctx, ctx, roombroker.Room{JoinURL: "https://telemost.yandex.ru/j/missing"}); err == nil {
		test.Fatal("uncreated room accepted")
	}
	room, err := provider.CreateRoom(ctx)
	if err != nil || room.ID == "" || !roombroker.ValidJoinURL(room.JoinURL) {
		test.Fatal("room creation", err)
	}
	first, err := provider.Connect(ctx, ctx, room)
	if err != nil {
		test.Fatal(err)
	}
	defer first.Close()
	second, err := provider.Connect(ctx, ctx, room)
	if err != nil {
		test.Fatal(err)
	}
	defer second.Close()
	for _, pair := range [][2]*Endpoint{{first, second}, {second, first}} {
		payload := []byte("a real framed packet")
		if err := pair[0].SendContext(ctx, payload); err != nil {
			test.Fatal(err)
		}
		received, err := pair[1].Recv(ctx)
		if err != nil || !bytes.Equal(received, payload) {
			test.Fatal("packet forwarding", err)
		}
	}
	if first.Stats().BytesSent == 0 || second.Stats().BytesReceived == 0 {
		test.Fatal("missing packet counters")
	}
	first.Close()
	if _, err := first.Recv(ctx); err == nil {
		test.Fatal("closed endpoint still receiving")
	}
}

func TestFramingRejectsInvalidSizes(test *testing.T) {
	for _, size := range []uint32{0, packetLimit + 1, ^uint32(0)} {
		var header [4]byte
		binary.BigEndian.PutUint32(header[:], size)
		if _, err := readFrame(bytes.NewReader(header[:])); err == nil {
			test.Fatal("invalid frame accepted")
		}
	}
	if err := writeFrame(&bytes.Buffer{}, nil); err == nil {
		test.Fatal("empty send accepted")
	}
}
