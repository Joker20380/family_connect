package tcpforward

import (
	"bytes"
	"context"
	"encoding/json"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"io"
	"net"
	"testing"
	"time"
)

func TestPackingMuxCreditProducerSilent(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	clientSession, serverSession := authenticatedPair(test, familysession.WithLabPacking(ctx, "B2"))
	payload := bytes.Repeat([]byte("packing-with-window-update"), 8192)
	port := muxFixture(test, func(connection *net.TCPConn) {
		header := make([]byte, 1)
		if _, err := io.ReadFull(connection, header); err != nil {
			return
		}
		if header[0] == 'D' {
			connection.Write(payload)
		} else {
			connection.Write(header)
		}
		connection.CloseWrite()
	})
	server, err := NewMux(ctx, serverSession, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	defer server.Close()
	client, err := NewMux(ctx, clientSession, false, MuxConfig{})
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	stream := muxOpen(test, ctx, client, port)
	if _, err = stream.Write([]byte("D")); err != nil {
		test.Fatal(err)
	}
	if err = stream.CloseWrite(); err != nil {
		test.Fatal(err)
	}
	time.Sleep(100 * time.Millisecond)
	received := make([]byte, len(payload))
	if _, err = io.ReadFull(stream, received); err != nil || !bytes.Equal(received, payload) {
		test.Fatal("credit update without new producer write", err)
	}
	if _, err = stream.Read(make([]byte, 1)); err != io.EOF {
		test.Fatal("bulk FIN", err)
	}
	stream.Close()
	small := muxOpen(test, ctx, client, port)
	started := time.Now()
	small.Write([]byte("E"))
	small.CloseWrite()
	actual := make([]byte, 1)
	if _, err = io.ReadFull(small, actual); err != nil || actual[0] != 'E' {
		test.Fatal("silent small round trip", err)
	}
	if _, err = small.Read(make([]byte, 1)); err != io.EOF {
		test.Fatal("small FIN", err)
	}
	small.Close()
	clientFinal, serverFinal := client.Stats(), server.Stats()
	result, _ := json.Marshal(map[string]any{"small_rtt_seconds": time.Since(started).Seconds(), "client": clientFinal, "server": serverFinal})
	test.Log(string(result))
	if clientFinal.ProtocolErrors != 0 || serverFinal.ProtocolErrors != 0 {
		test.Fatal("protocol")
	}
}
