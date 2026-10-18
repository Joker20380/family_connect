package telemost

import (
	"encoding/binary"
	"sync"
	"sync/atomic"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

type outboundFrame struct {
	data  []byte
	point sessiontrace.Boundary
}

func fragmentBoundary(data []byte) sessiontrace.Boundary {
	point := sessiontrace.Boundary{}
	if len(data) < fragmentHeaderLen {
		return point
	}
	point.Sender, point.Message = binary.BigEndian.Uint32(data), binary.BigEndian.Uint32(data[4:])
	point.Fragment, point.Total = binary.BigEndian.Uint32(data[8:]), binary.BigEndian.Uint32(data[12:])
	if point.Total == 0 || point.Total > maxFragmentsPerMessage || point.Fragment >= point.Total {
		return sessiontrace.Boundary{}
	}
	point.MessageKnown = true
	if point.Fragment == 0 {
		point.DataSequence, point.DataKnown = reliablestream.DataSequencePrefix(data[fragmentHeaderLen:], binary.BigEndian.Uint32(data[16:]))
	}
	return point
}

type rtpBoundary struct {
	correlationOnly bool
	track           uint32
	point           sessiontrace.Boundary
	trace           *sessiontrace.Recorder
	stage           string
	direction       string
}

func (observer *rtpBoundary) flush(result string) {
	if observer.point.Packets == 0 {
		return
	}
	observer.point.Stage, observer.point.Direction, observer.point.Result = observer.stage, observer.direction, result
	if observer.correlationOnly {
		observer.trace.CorrelationMedia(observer.point)
	} else {
		observer.trace.Boundary(observer.point)
	}
	observer.point = sessiontrace.Boundary{}
}

func (observer *rtpBoundary) packet(header *rtp.Header, payload []byte, result string) {
	if observer.trace == nil || (observer.correlationOnly && !sessiontrace.CorrelationEnabled()) {
		return
	}
	if observer.point.Packets > 0 && observer.point.Timestamp != header.Timestamp {
		observer.flush("incomplete")
	}
	if observer.point.Packets == 0 {
		var descriptor codecs.VP8Packet
		if data, err := descriptor.Unmarshal(payload); err == nil && descriptor.S == 1 && descriptor.PID == 0 {
			if fragment, valid := decodeVP8Frame(data); valid {
				observer.point = fragmentBoundary(fragment)
			}
			observer.point.RecordPicture(descriptor.I == 1, descriptor.PictureID)
		}
		if observer.direction == "tx" {
			observer.point = observer.trace.MessageAttempt(observer.point)
		}
		observer.point.FrameKnown, observer.point.Timestamp, observer.point.FirstRTP = true, header.Timestamp, header.SequenceNumber
		observer.point.MediaTrack = observer.track
	}
	observer.point.LastRTP = header.SequenceNumber
	observer.point.Packets++
	if header.Marker || result != "ok" {
		observer.flush(result)
	}
}

type boundaryFactory struct {
	tracks atomic.Uint32
	trace  *sessiontrace.Recorder
	writes *atomic.Uint64
}

func (factory *boundaryFactory) NewInterceptor(string) (interceptor.Interceptor, error) {
	return &boundaryInterceptor{factory: factory}, nil
}

type boundaryInterceptor struct {
	interceptor.NoOp
	factory *boundaryFactory
}

func (boundary *boundaryInterceptor) BindLocalStream(info *interceptor.StreamInfo, writer interceptor.RTPWriter) interceptor.RTPWriter {
	if info.MimeType != "video/VP8" {
		return writer
	}
	var mutex sync.Mutex
	observer := rtpBoundary{trace: boundary.factory.trace, stage: "rtp_written", direction: "tx", track: boundary.factory.tracks.Add(1)}
	return interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, attributes interceptor.Attributes) (int, error) {
		mutex.Lock()
		defer mutex.Unlock()
		count, err := writer.Write(header, payload, attributes)
		result := "ok"
		if err != nil {
			result = "write_error"
		} else if count <= 0 {
			result = "no_rtp"
		} else {
			boundary.factory.writes.Add(1)
		}
		observer.packet(header, payload, result)
		return count, err
	})
}
