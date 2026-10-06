package reliablestream

import (
	"bytes"
	"encoding/hex"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestForensicsPreservesReliableWireAndConfig(test *testing.T) {
	config := Config{Payload: 16384, SendWindow: 8, ReceiveWindow: 16, RTO: time.Second, MaxRetries: 8, MaxAge: 20 * time.Second}
	if DefaultConfig() != config {
		test.Fatal("transport defaults changed")
	}
	for _, sample := range []struct {
		packet frame
		golden string
	}{
		{frame{kind: dataFrame, source: epoch{1}, target: epoch{2}, seq: 19, data: []byte{0xaa, 0xbb}}, "46525331020000020100000000000000000000000000000002000000000000000000000000000000000000000000001300000000000000000000000000000000aabb"},
		{frame{kind: ackFrame, source: epoch{2}, target: epoch{1}, ack: 20, bits: 127}, "46525331030000000200000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000140000007f00000000"},
	} {
		expected, err := hex.DecodeString(sample.golden)
		if err != nil || !bytes.Equal(encode(sample.packet), expected) {
			test.Fatal("Reliable wire golden mismatch", err)
		}
		recorder := sessiontrace.New(strings.Repeat("a", 64), nil)
		recorder.RecordConsumed(19, 20, 127)
		recorder.RecordBaseAdvanced(20, 127)
		if !bytes.Equal(encode(sample.packet), expected) {
			test.Fatal("forensic callbacks changed Reliable wire")
		}
	}
}
