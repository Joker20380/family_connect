package wholedevice

import (
	"context"
	"io"
	"testing"
	"time"
)

func TestServiceStreamIsolationQuotaAndCancellation(test *testing.T) {
	plane := &testPlane{done: make(chan struct{})}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	for _, name := range []string{"localhost", "127.0.0.1:80", "chat-api.family-connect.invalid", "chat-mailbox:1", ""} {
		if stream, err := session.OpenService(ctx, name); err == nil {
			stream.Close()
			test.Fatalf("untrusted service accepted: %s", name)
		}
	}
	sibling, err := plane.Open(ctx, "93.184.216.34", 443)
	if err != nil {
		test.Fatal(err)
	}
	defer sibling.Close()
	streams := []Stream{}
	for index := 0; index < 4; index++ {
		stream, err := session.OpenService(ctx, "chat-mailbox")
		if err != nil {
			test.Fatal(err)
		}
		streams = append(streams, stream)
	}
	if _, err := session.OpenService(ctx, "chat-api"); err == nil {
		test.Fatal("unbounded service streams")
	}
	for _, stream := range streams {
		stream.Reset()
		stream.Close()
	}
	if session.Failed() {
		test.Fatal("chat release cancelled shared VPN consumer")
	}
	go func() { sibling.Write([]byte("vpn-consumer")) }()
	buffer := make([]byte, 12)
	if _, err := io.ReadFull(sibling, buffer); err != nil || string(buffer) != "vpn-consumer" {
		test.Fatalf("sibling stopped: %q %v", buffer, err)
	}
	bounded, stop := context.WithCancel(ctx)
	stream, err := session.OpenService(bounded, "chat-api")
	if err != nil {
		test.Fatal(err)
	}
	stop()
	if _, err := stream.Read(buffer); err == nil {
		test.Fatal("cancel did not end pending read")
	}
	stream.Reset()
	if session.Failed() {
		test.Fatal("stream cancellation closed owner")
	}
	session.Close()
	if _, err := session.OpenService(ctx, "chat-api"); err == nil {
		test.Fatal("closed carrier accepted stale open")
	}
}
