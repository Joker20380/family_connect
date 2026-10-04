package telemost

import (
	"bytes"
	"encoding/binary"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

func diagnosticData() []byte {
	data := make([]byte, reliablestream.HeaderSize+16384)
	copy(data, "FRS1")
	data[4] = 2
	binary.BigEndian.PutUint16(data[6:], 16384)
	copy(data[reliablestream.HeaderSize:], bytes.Repeat([]byte("synthetic-private"), 1000))
	return data
}

func TestFragmentDeliveryMappingAndMissingHeader(test *testing.T) {
	fragments, _ := encodeFragments(1, 42, diagnosticData())
	clock := time.Now()
	assembler := newReassembler(2, nil)
	assembler.now = func() time.Time { return clock }
	assembler.ingest(fragments[1])
	value := assembler.delivery()
	if value.Pending.Message != 42 || value.Pending.Total != 3 || value.Pending.Mask != 2 || value.Pending.DataKnown || value.Assembly.Pending != 1 {
		test.Fatal("missing first fragment must not invent sequence")
	}
	assembler.ingest(fragments[0])
	value = assembler.delivery()
	if !value.Pending.DataKnown || value.Pending.DataSequence != 0 || value.Pending.Mask != 3 {
		test.Fatal("sequence zero or partial mask missing")
	}
	assembler.ingest(fragments[2])
	value = assembler.delivery()
	if value.Pending != nil || value.Received.Message != 42 || value.Received.Mask != 7 || value.Assembly.Completed != 1 || value.Assembly.Fragments != 3 {
		test.Fatal("CRC-complete message missing")
	}
	value.Received.Message = 999
	if assembler.delivery().Received.Message != 42 {
		test.Fatal("received alias")
	}
	queued := advanceFragment(nil, fragments[0])
	for _, fragment := range fragments[1:] {
		queued = advanceFragment(queued, fragment)
	}
	if queued == nil || queued.Message != 42 || queued.Mask != 7 || queued.DataSequence != 0 || !queued.DataKnown {
		test.Fatal("transmit and receive mapping disagree")
	}
	other, _ := encodeFragments(1, 43, diagnosticData())
	assembler.ingest(other[1])
	clock = clock.Add(reassemblyTimeout)
	assembler.prune()
	if assembler.delivery().Assembly.Expired != 1 || assembler.delivery().Pending != nil {
		test.Fatal("expiry decision missing")
	}
}

func TestAssemblyRejectCountersDoNotChangeDelivery(test *testing.T) {
	assembler := newReassembler(2, func([]byte) { test.Fatal("corruption delivered") })
	fragments, _ := encodeFragments(1, 1, diagnosticData())
	assembler.ingest(nil)
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[1])
	corrupt, _ := encodeFragments(1, 2, []byte("crc-control"))
	corrupt[0][fragmentHeaderLen] ^= 1
	assembler.ingest(corrupt[0])
	value := assembler.delivery().Assembly
	if value.Malformed != 1 || value.Duplicate != 1 || value.Recent != 1 || value.CRCFailed != 1 || value.Completed != 0 {
		test.Fatal("reject causes not separated", value)
	}
	for message := uint32(3); message < 3+maxPendingMessages+1; message++ {
		fragments, _ := encodeFragments(1, message, diagnosticData())
		assembler.ingest(fragments[0])
	}
	if assembler.delivery().Assembly.Capacity != 1 || assembler.delivery().Assembly.Pending != maxPendingMessages {
		test.Fatal("capacity behavior changed")
	}
}
