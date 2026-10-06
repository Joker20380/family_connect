package telemost

import "testing"

func TestPerformanceSnapshotQueues(test *testing.T) {
	session := &Session{sendQueue: make(chan outboundFrame, 3), recvQueue: make(chan []byte, 2)}
	session.sendQueue <- outboundFrame{data: []byte{1}}
	result := session.PerformanceSnapshot()
	if result["send_queue_frames"] != 1 || result["send_queue_capacity"] != 3 || result["receive_queue_messages"] != 0 {
		test.Fatal("queue snapshot must preserve bounds")
	}
}
