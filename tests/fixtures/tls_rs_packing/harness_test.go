package main

import (
	"bytes"
	"encoding/binary"
	"io"
	"net"
	"testing"
	"time"
)

func TestPackingHarnessSmallEcho(test *testing.T) {
	server, client := net.Pipe()
	defer server.Close()
	defer client.Close()
	client.SetDeadline(time.Now().Add(time.Second))
	payload := hostPayload()
	done := make(chan error, 1)
	go func() { done <- hostFixtureRequest(server, payload) }()
	request := binary.BigEndian.AppendUint32([]byte{'E'}, 32)
	request = append(request, payload[:32]...)
	if _, err := client.Write(request); err != nil {
		test.Fatal(err)
	}
	actual := make([]byte, 32)
	if _, err := io.ReadFull(client, actual); err != nil || !bytes.Equal(actual, payload[:32]) {
		test.Fatal(err)
	}
	if err := <-done; err != nil {
		test.Fatal(err)
	}
}
