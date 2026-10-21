package tcpforward

import "time"

type labMuxEvent struct {
	NS                                              int64
	Kind                                            string
	ID                                              uint32
	Bytes, Credit, Ready, Queued, Buffered, Pending int
}

type labMuxObservation struct {
	Started                                                      time.Time
	Events                                                       []labMuxEvent
	Dropped                                                      uint64
	WriterLockNS, WriterLockMaxNS, WriterSendNS, WriterSendMaxNS int64
}

func (mux *Mux) labEventLocked(kind string, id uint32, size int) {
	if mux.lab.Started.IsZero() {
		mux.lab.Started = time.Now()
	}
	if len(mux.lab.Events) >= 32768 {
		mux.lab.Dropped++
		return
	}
	event := labMuxEvent{NS: time.Since(mux.lab.Started).Nanoseconds(), Kind: kind, ID: id, Bytes: size}
	if stream := mux.streams[id]; stream != nil {
		event.Credit, event.Ready, event.Queued = stream.sendCredit, stream.perf.ReadyBytes, len(stream.send)
		event.Buffered, event.Pending = stream.used, stream.creditPending
	}
	mux.lab.Events = append(mux.lab.Events, event)
}

func (mux *Mux) LabObservation() labMuxObservation {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	result := mux.lab
	result.Events = append([]labMuxEvent(nil), result.Events...)
	return result
}
