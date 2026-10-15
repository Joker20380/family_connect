//go:build fc_owner_diagnostic

package reliablestream

import (
	"bytes"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"testing"
)

func TestACKObservationDoesNotChangeWire(test *testing.T) {
	packet := frame{kind: ackFrame, source: epoch{1}, target: epoch{2}, ack: 20, bits: 3}
	before := encode(packet)
	packet.observation = sessiontrace.StampACK()
	if !bytes.Equal(before, encode(packet)) {
		test.Fatal("observation modified wire")
	}
	decoded, err := decode(encode(packet))
	if err != nil || decoded.observation.CreatedNS != 0 {
		test.Fatal("observation leaked onto wire", err)
	}
}
