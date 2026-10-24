package familysession

import (
	"context"
	"encoding/binary"
	"time"
)

const BatchMessageHeaderSize = 12
const MaxBatchMessages = 32
const tlsRecordHeaderSize = 5
const tls13ContentTypeSize = 1
const tls13TagSize = 16
const MaxBatchPlaintext = (16 << 10) - tlsRecordHeaderSize - tls13ContentTypeSize - tls13TagSize

func (session *Session) SendBatchContext(ctx context.Context, payloads [][]byte) (failure error) {
	defer func() { traceFailure(ctx, session.trace, failure) }()
	session.sendMu.Lock()
	defer session.sendMu.Unlock()
	size := 0
	valid := len(payloads) > 0 && len(payloads) <= MaxBatchMessages && uint64(len(payloads)) <= ^uint64(0)-session.sendSequence
	for _, payload := range payloads {
		if !valid {
			break
		}
		if len(payload) > MaxPayload || len(payload) > MaxBatchPlaintext-BatchMessageHeaderSize-size {
			valid = false
			break
		}
		size += BatchMessageHeaderSize + len(payload)
	}
	if !valid || !time.Now().Before(session.expiry) || ctx.Err() != nil {
		session.traceStop(ctx, "FAMILY_CONTRACT")
		session.stream.stop()
		return ErrRejected
	}
	deadline := session.expiry
	if bound, ok := ctx.Deadline(); ok {
		deadline = minTime(deadline, bound)
	}
	session.connection.SetWriteDeadline(deadline)
	stop := context.AfterFunc(ctx, func() { session.traceStop(ctx, "FAMILY_CONTEXT"); session.stream.stop() })
	defer stop()
	message := make([]byte, size)
	offset := 0
	for index, payload := range payloads {
		binary.BigEndian.PutUint32(message[offset:], uint32(len(payload)))
		binary.BigEndian.PutUint64(message[offset+4:], session.sendSequence+uint64(index))
		copy(message[offset+BatchMessageHeaderSize:], payload)
		offset += BatchMessageHeaderSize + len(payload)
	}
	if _, err := session.connection.Write(message); err != nil {
		session.traceStop(ctx, "FAMILY_WRITE")
		session.stream.stop()
		return err
	}
	session.sendSequence += uint64(len(payloads))
	return nil
}
