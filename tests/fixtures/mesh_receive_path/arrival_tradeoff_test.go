package telemost

import (
	"bytes"
	"fmt"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestArrivalDeadlineTradeoff(test *testing.T) {
	for _, delay := range []int{-1, 99, 100, 124, 125, 126, 500} {
		test.Run(fmt.Sprint(delay), func(test *testing.T) {
			replayNow, replayBudget = time.Now(), 100*time.Millisecond
			payload := bytes.Repeat([]byte{67}, 3000)
			fragments, err := encodeFragments(1, 1, payload)
			if err != nil {
				test.Fatal(err)
			}
			payloader := codecs.VP8Payloader{}
			packets := payloader.Payload(1200, encodeVP8DataFrame(fragments[0]))
			if len(packets) != 3 {
				test.Fatal("shape")
			}
			buffer := newReorderBuffer()
			state := vp8FrameState{}
			var result [][]byte
			assembler := newReassembler(99, func(data []byte) { result = append(result, data) })
			deliver := func(packet *rtp.Packet) {
				if frame := state.process(packet); frame != nil {
					if fragment, ok := decodeVP8Frame(frame); ok {
						assembler.ingest(fragment)
					}
				}
			}
			push := func(index int) {
				buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: uint16(index + 1), Timestamp: 1, Marker: index == 2}, Payload: packets[index]}, deliver)
			}
			push(0)
			push(2)
			if delay < 0 {
				replayNow = replayNow.Add(time.Hour)
				if len(buffer.pkts) != 1 || len(result) != 0 {
					test.Fatal("baseline unexpectedly autonomous")
				}
				return
			}
			replayNow = replayNow.Add(time.Duration(delay) * time.Millisecond)
			push(1)
			if len(result) != 1 || !bytes.Equal(result[0], payload) || len(buffer.pkts) != 0 {
				test.Fatal("baseline accepts overdue hole before skip")
			}
		})
	}
}
