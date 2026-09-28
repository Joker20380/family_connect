package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"io"
	"net"
	"os"
	"strings"
	"time"

	"golang.org/x/net/dns/dnsmessage"
)

type dnsCall struct {
	ctx      context.Context
	cancel   context.CancelFunc
	query    []byte
	response []byte
	done     bool
	err      error
}

func validDNS(payload []byte, response bool) (dnsmessage.Message, error) {
	var message dnsmessage.Message
	if len(payload) >= 12 && (binary.BigEndian.Uint16(payload[4:6]) != 1 || uint32(binary.BigEndian.Uint16(payload[6:8]))+uint32(binary.BigEndian.Uint16(payload[8:10]))+uint32(binary.BigEndian.Uint16(payload[10:12])) > 128) {
		return message, ErrDNS
	}
	if len(payload) < 12 || len(payload) > MuxMaxDNSMessage || message.Unpack(payload) != nil || message.Header.Response != response || message.Header.OpCode != 0 || len(message.Questions) != 1 || message.Questions[0].Class != dnsmessage.ClassINET {
		return message, ErrDNS
	}
	if !response && (len(message.Answers) != 0 || len(message.Authorities) != 0 || message.Header.RCode != 0) {
		return message, ErrDNS
	}
	return message, nil
}

func matchesDNS(query, response []byte) bool {
	request, err := validDNS(query, false)
	if err != nil {
		return false
	}
	answer, err := validDNS(response, true)
	if err != nil {
		return false
	}
	return request.Header.ID == answer.Header.ID && request.Questions[0] == answer.Questions[0]
}

func dnsFrame(kind byte, id uint32, payload []byte) muxFrame {
	encoded := make([]byte, 4+len(payload))
	binary.BigEndian.PutUint32(encoded, id)
	copy(encoded[4:], payload)
	return muxFrame{kind, 0, encoded}
}

func (mux *Mux) QueryDNS(parent context.Context, query []byte) ([]byte, error) {
	if _, err := validDNS(query, false); err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(parent, 5*time.Second)
	defer cancel()
	mux.mu.Lock()
	defer mux.mu.Unlock()
	if mux.server || mux.ctx.Err() != nil || ctx.Err() != nil {
		return nil, ErrReset
	}
	if len(mux.dns) >= MuxMaxDNS {
		return nil, ErrStreamLimit
	}
	if mux.dnsNext > muxMaxID {
		return nil, ErrIDExhausted
	}
	id := mux.dnsNext
	mux.dnsNext++
	call := &dnsCall{ctx: ctx, cancel: cancel, query: bytes.Clone(query)}
	mux.dns[id] = call
	mux.stats.DNSRequests++
	mux.controlLocked(dnsFrame(muxDNSQuery, id, query))
	defer func() { delete(mux.dns, id); mux.measureLocked() }()
	for !call.done && ctx.Err() == nil && mux.ctx.Err() == nil {
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-ctx.Done():
		case <-mux.ctx.Done():
		}
		mux.mu.Lock()
	}
	if call.done {
		return call.response, call.err
	}
	mux.controlLocked(dnsFrame(muxDNSCancel, id, nil))
	if ctx.Err() != nil {
		if ctx.Err() == context.DeadlineExceeded {
			mux.stats.DNSTimeouts++
		}
		return nil, ctx.Err()
	}
	return nil, ErrReset
}

func (mux *Mux) dnsFrameLocked(frame muxFrame) {
	id, payload := binary.BigEndian.Uint32(frame.payload), frame.payload[4:]
	call := mux.dns[id]
	if mux.server {
		switch frame.kind {
		case muxDNSCancel:
			if call != nil {
				call.cancel()
			}
		case muxDNSQuery:
			if id <= mux.dnsLast {
				mux.stats.ProtocolErrors++
				return
			}
			mux.dnsLast = id
			_, err := validDNS(payload, false)
			if err != nil || len(mux.dns) >= MuxMaxDNS || len(mux.dnsJobs) >= cap(mux.dnsJobs) {
				mux.stats.DNSErrors++
				mux.controlLocked(dnsFrame(muxDNSError, id, nil))
				return
			}
			ctx, cancel := context.WithTimeout(mux.ctx, 5*time.Second)
			call = &dnsCall{ctx: ctx, cancel: cancel, query: bytes.Clone(payload)}
			mux.dns[id] = call
			mux.stats.DNSRequests++
			mux.dnsJobs <- struct{}{}
			mux.workers.Add(1)
			go mux.resolveDNS(id, call)
		default:
			mux.stats.ProtocolErrors++
		}
		return
	}
	if call == nil || call.done {
		mux.stats.ProtocolErrors++
		return
	}
	if frame.kind == muxDNSResponse && matchesDNS(call.query, payload) {
		call.response = bytes.Clone(payload)
		mux.stats.DNSResponses++
	} else {
		call.err = ErrDNS
		mux.stats.DNSErrors++
	}
	call.done = true
}

func (mux *Mux) resolveDNS(id uint32, call *dnsCall) {
	defer mux.workers.Done()
	defer func() { <-mux.dnsJobs }()
	defer call.cancel()
	response, err := mux.exchange(call.ctx, call.query)
	mux.mu.Lock()
	defer mux.mu.Unlock()
	delete(mux.dns, id)
	if mux.ctx.Err() != nil || call.ctx.Err() == context.Canceled {
		return
	}
	if err != nil || !matchesDNS(call.query, response) {
		mux.stats.DNSErrors++
		if call.ctx.Err() == context.DeadlineExceeded {
			mux.stats.DNSTimeouts++
		}
		mux.controlLocked(dnsFrame(muxDNSError, id, nil))
	} else {
		mux.stats.DNSResponses++
		mux.controlLocked(dnsFrame(muxDNSResponse, id, response))
	}
}

func (mux *Mux) exchangeDNS(ctx context.Context, query []byte) ([]byte, error) {
	upstream := mux.config.DNSUpstream
	if upstream == "" {
		file, err := os.Open("/etc/resolv.conf")
		if err != nil {
			return nil, ErrDNS
		}
		encoded, err := io.ReadAll(io.LimitReader(file, 65537))
		file.Close()
		if err != nil || len(encoded) > 65536 {
			return nil, ErrDNS
		}
		for _, line := range strings.Split(string(encoded), "\n") {
			fields := strings.Fields(line)
			if len(fields) >= 2 && fields[0] == "nameserver" && net.ParseIP(fields[1]) != nil {
				upstream = net.JoinHostPort(fields[1], "53")
				break
			}
		}
	}
	if upstream == "" {
		return nil, ErrDNS
	}
	connection, err := (&net.Dialer{}).DialContext(ctx, "tcp", upstream)
	if err != nil {
		return nil, ErrDNS
	}
	defer connection.Close()
	stop := context.AfterFunc(ctx, func() { connection.Close() })
	defer stop()
	deadline, _ := ctx.Deadline()
	connection.SetDeadline(deadline)
	encoded := make([]byte, len(query)+2)
	binary.BigEndian.PutUint16(encoded, uint16(len(query)))
	copy(encoded[2:], query)
	if err := writeTarget(connection, encoded, &Metrics{}); err != nil {
		return nil, ErrDNS
	}
	header := make([]byte, 2)
	if _, err := io.ReadFull(connection, header); err != nil {
		return nil, ErrDNS
	}
	length := int(binary.BigEndian.Uint16(header))
	if length < 12 || length > MuxMaxDNSMessage {
		return nil, ErrDNS
	}
	response := make([]byte, length)
	if _, err := io.ReadFull(connection, response); err != nil || !matchesDNS(query, response) {
		return nil, ErrDNS
	}
	return response, nil
}
