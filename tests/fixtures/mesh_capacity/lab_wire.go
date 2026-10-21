package telemost

import (
	"errors"
	"os"
	"strconv"
	"sync/atomic"

	"github.com/pion/interceptor"
	"github.com/pion/rtcp"
	"github.com/pion/rtp"
)

var labWireBudget atomic.Uint64
var labWireRTP atomic.Uint64
var labWireRTCP atomic.Uint64
var labWirePackets atomic.Uint64
var labWireStopped atomic.Bool

type labWireFactory struct{}
type labWireInterceptor struct{ interceptor.NoOp }

func (*labWireFactory) NewInterceptor(string) (interceptor.Interceptor, error) {
	return &labWireInterceptor{}, nil
}

func labWireReserve(size int) bool {
	limit, _ := strconv.ParseUint(os.Getenv("FC_LAB_WIRE_LIMIT"), 10, 64)
	if limit == 0 {
		labWireStopped.Store(true)
		return false
	}
	for {
		before := labWireBudget.Load()
		if before+uint64(size+64) > limit {
			labWireStopped.Store(true)
			return false
		}
		if labWireBudget.CompareAndSwap(before, before+uint64(size+64)) {
			return true
		}
	}
}

func (*labWireInterceptor) BindLocalStream(_ *interceptor.StreamInfo, writer interceptor.RTPWriter) interceptor.RTPWriter {
	return interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, attributes interceptor.Attributes) (int, error) {
		size := header.MarshalSize() + len(payload)
		if !labWireReserve(size) {
			return 0, errors.New("laboratory wire budget exhausted")
		}
		labWireRTP.Add(uint64(size))
		labWirePackets.Add(1)
		return writer.Write(header, payload, attributes)
	})
}

func (*labWireInterceptor) BindRTCPWriter(writer interceptor.RTCPWriter) interceptor.RTCPWriter {
	return interceptor.RTCPWriterFunc(func(packets []rtcp.Packet, attributes interceptor.Attributes) (int, error) {
		size := 0
		for _, packet := range packets {
			size += packet.MarshalSize()
		}
		if !labWireReserve(size) {
			return 0, errors.New("laboratory wire budget exhausted")
		}
		labWireRTCP.Add(uint64(size))
		return writer.Write(packets, attributes)
	})
}

func labWireSnapshot() map[string]any {
	return map[string]any{"rtp_bytes": labWireRTP.Load(), "rtcp_bytes": labWireRTCP.Load(), "rtp_packets": labWirePackets.Load(), "conservative_bytes": labWireBudget.Load(), "stopped": labWireStopped.Load()}
}
