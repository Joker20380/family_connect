package telemost

import (
	"bytes"
	"context"
	"testing"
)

func TestGatewayRetainedQueueAfterClose(test *testing.T) {
	session, err := New(context.Background(), Config{RoomURL: "synthetic-resource-no-provider"})
	if err != nil {
		test.Fatal(err)
	}
	for index := 0; index < 64; index++ {
		session.deliver(bytes.Repeat([]byte{byte(index)}, MaxMessageSize))
	}
	if err := session.Close(); err != nil {
		test.Fatal(err)
	}
	select {
	case <-session.cleanupDone:
	default:
		test.Fatal("cleanup incomplete")
	}
	retained := 0
	for len(session.recvQueue) > 0 {
		retained += len(unpackReceive(context.Background(), <-session.recvQueue))
	}
	test.Logf("cleanup_done=true retained_payload_before_fixture_drain=%d capacity=%d; Close does not promise zero queue references", retained, cap(session.recvQueue))
	if retained != 64*MaxMessageSize {
		test.Fatal("unexpected retained resource accounting", retained)
	}
}
