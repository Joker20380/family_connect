package familysession

import (
	"context"
	"testing"
	"time"
)

func TestPackingDrainRejectsTerminal(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	left, right := pair()
	clientProfile, serverProfile := profiles(test)
	ready := make(chan *Session, 1)
	go func() {
		session, _ := Open(WithLabPacking(ctx, "B2"), right, encoded(serverProfile), true)
		ready <- session
	}()
	client, err := Open(WithLabPacking(ctx, "B2"), left, encoded(clientProfile), false)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	server := <-ready
	if server == nil {
		test.Fatal("handshake")
	}
	defer server.Close()
	cancel()
	deadline := time.Now().Add(time.Second)
	for client.ReliabilityStats().Terminal == "" && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if client.ReliabilityStats().Terminal == "" {
		test.Fatal("missing terminal")
	}
	if err = client.LabDrain(context.Background()); err == nil {
		test.Fatal("terminal RS with zero depth incorrectly reported drained")
	}
}
