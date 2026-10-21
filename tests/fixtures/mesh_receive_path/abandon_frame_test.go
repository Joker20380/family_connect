package telemost

import (
	"bytes"
	"sync"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestDiscardedFrameReleasesAssemblyAndRetry(test *testing.T) {
	for generation := 0; generation < 3; generation++ {
		var output [][]byte
		assembler := newReassembler(2,func(data []byte){output=append(output,bytes.Clone(data))})
		state := vp8FrameState{onDiscard:assembler.discardFrame}
		payload:=bytes.Repeat([]byte{0x5a},16384+44)
		sequence:=uint16(65520)
		payloader:=&codecs.VP8Payloader{}
		for message:=uint32(1);message<=24;message++ {
			fragments,err:=encodeFragments(1,message,payload);if err!=nil{test.Fatal(err)}
			for fragmentIndex,fragment:=range fragments {
				packets:=payloader.Payload(1200,encodeVP8DataFrame(fragment))
				for packetIndex,body:=range packets {
					packet:=&rtp.Packet{Header:rtp.Header{SequenceNumber:sequence,Timestamp:message*9000+uint32(fragmentIndex)*2970,Marker:packetIndex==len(packets)-1},Payload:body}
					sequence++
					if message<24&&fragmentIndex==int(message%2)&&packetIndex==1{continue}
					if fragment,valid:=decodeVP8Frame(state.process(packet));valid{assembler.ingest(fragment)}
				}
			}
			if len(assembler.builds)!=0{test.Fatal("irrecoverable frame retained partial assembly",message)}
		}
		if len(output)!=1||!bytes.Equal(output[0],payload)||assembler.metrics.Capacity!=0{test.Fatal("retry did not recover exactly once without local capacity loss")}
		if len(assembler.recent)!=24{test.Fatal("discarded messages not fenced against late fragments")}
		test.Logf("generation=%d irrecoverable_attempts=23 pending=0 intact_retry_delivered=1 capacity=0",generation)
	}
}

func TestDiscardedDuplicateCannotInvalidateReceivedFragment(test *testing.T) {
	payload:=bytes.Repeat([]byte{0x62},16000)
	fragments,err:=encodeFragments(1,10,payload);if err!=nil{test.Fatal(err)}
	var output []byte
	assembler:=newReassembler(2,func(data []byte){output=bytes.Clone(data)})
	assembler.ingest(fragments[0])
	assembler.discardFrame(encodeVP8DataFrame(fragments[0][:100]))
	if len(assembler.builds)!=1{test.Fatal("already valid fragment invalidated")}
	assembler.ingest(fragments[1])
	if !bytes.Equal(output,payload){test.Fatal("duplicate discard prevented complete delivery")}
}

func TestDiscardedFrameExpiryBoundsAndConcurrentPrune(test *testing.T) {
	payload:=bytes.Repeat([]byte{0x71},16000)
	assembler:=newReassembler(2,func([]byte){test.Error("partial message escaped")})
	for message:=uint32(1);message<=maxRecentMessages+10;message++{
		fragments,err:=encodeFragments(1,message,payload);if err!=nil{test.Fatal(err)}
		assembler.discardFrame(encodeVP8DataFrame(fragments[0][:100]))
	}
	if len(assembler.recent)!=maxRecentMessages||len(assembler.builds)!=0{test.Fatal("discard history unbounded")}
	assembler.now=func()time.Time{return time.Now().Add(11*time.Second)}
	assembler.prune()
	if len(assembler.recent)!=0{test.Fatal("discard history never expires")}
	fragments,err:=encodeFragments(1,100,payload);if err!=nil{test.Fatal(err)}
	var workers sync.WaitGroup
	for worker:=0;worker<4;worker++{
		workers.Add(1)
		go func(){defer workers.Done();for index:=0;index<100;index++{assembler.ingest(fragments[0]);assembler.discardFrame(encodeVP8DataFrame(fragments[1][:100]));assembler.prune();assembler.delivery()}}()
	}
	workers.Wait()
}
