package bootstrap

import (
	"bytes"
	"context"
	"crypto/rand"
	"errors"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

const envelopeSize = 69
const packetLimit = 33000
const ExchangeTimeout = 120 * time.Second
const ConnectTimeout = 45 * time.Second
const AdmissionTimeout = 30 * time.Second

type packet struct {
	kind           byte
	client, server [32]byte
	data           []byte
}

func encodePacket(message packet) []byte {
	raw := make([]byte, envelopeSize+len(message.data))
	copy(raw, "FCB1")
	raw[4] = message.kind
	copy(raw[5:37], message.client[:])
	copy(raw[37:69], message.server[:])
	copy(raw[69:], message.data)
	return raw
}

func decodePacket(raw []byte) (packet, bool) {
	var message packet
	if len(raw) < envelopeSize || len(raw) > envelopeSize+packetLimit || !bytes.Equal(raw[:4], []byte("FCB1")) {
		return message, false
	}
	message.kind = raw[4]
	copy(message.client[:], raw[5:37])
	copy(message.server[:], raw[37:69])
	message.data = raw[69:]
	if message.client == [32]byte{} {
		return packet{}, false
	}
	switch message.kind {
	case 'O':
		return message, len(message.data) == 0 && message.server == [32]byte{}
	case 'A':
		return message, len(message.data) == 0 && message.server != [32]byte{}
	case 'C', 'S':
		return message, len(message.data) > 0 && message.server != [32]byte{}
	default:
		return packet{}, false
	}
}

type lease struct {
	carrier        familysession.PacketEndpoint
	client, server [32]byte
	incoming       chan []byte
	done           chan struct{}
	finished       chan struct{}
	once           sync.Once
	sendMu         *sync.Mutex
	serverSide     bool
	lastAccept     time.Time
}

func (session *lease) Close() error { session.once.Do(func() { close(session.done) }); return nil }
func (session *lease) SendContext(ctx context.Context, data []byte) error {
	if len(data) == 0 || len(data) > packetLimit {
		return roombroker.Code("packet_rejected")
	}
	select {
	case <-session.done:
		return roombroker.Code("exchange_closed")
	default:
	}
	kind := byte('C')
	if session.serverSide {
		kind = 'S'
	}
	session.sendMu.Lock()
	defer session.sendMu.Unlock()
	return session.carrier.SendContext(ctx, encodePacket(packet{kind, session.client, session.server, data}))
}
func (session *lease) Recv(ctx context.Context) ([]byte, error) {
	select {
	case data := <-session.incoming:
		return data, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-session.done:
		return nil, roombroker.Code("exchange_closed")
	}
}

func connectLease(ctx context.Context, carrier familysession.PacketEndpoint) (*lease, error) {
	session := &lease{carrier: carrier, incoming: make(chan []byte, 16), done: make(chan struct{}), sendMu: &sync.Mutex{}}
	if _, err := rand.Read(session.client[:]); err != nil {
		return nil, err
	}
	nextOpen := time.Time{}
	for {
		if ctx.Err() != nil {
			return nil, roombroker.Code("seed_busy_or_unavailable")
		}
		if !time.Now().Before(nextOpen) {
			if err := carrier.SendContext(ctx, encodePacket(packet{kind: 'O', client: session.client})); err != nil {
				return nil, roombroker.Code("seed_unavailable")
			}
			nextOpen = time.Now().Add(time.Second)
		}
		poll, cancel := context.WithDeadline(ctx, nextOpen)
		raw, err := carrier.Recv(poll)
		cancel()
		if errors.Is(err, context.DeadlineExceeded) && ctx.Err() == nil {
			continue
		}
		if err != nil {
			return nil, roombroker.Code("seed_busy_or_unavailable")
		}
		message, ok := decodePacket(raw)
		if ok && message.kind == 'A' && message.client == session.client {
			session.server = message.server
			return session, nil
		}
	}
}

func readLease(ctx context.Context, session *lease) {
	defer session.Close()
	for {
		raw, err := session.carrier.Recv(ctx)
		if err != nil {
			return
		}
		message, ok := decodePacket(raw)
		if !ok || message.kind != 'S' || message.client != session.client || message.server != session.server {
			continue
		}
		select {
		case session.incoming <- message.data:
		case <-ctx.Done():
			return
		case <-session.done:
			return
		default:
			return
		}
	}
}

func ServeCarrier(ctx context.Context, carrier familysession.PacketEndpoint, exchange func(context.Context, familysession.PacketEndpoint)) error {
	ctx, cancel := context.WithCancel(ctx)
	var workers sync.WaitGroup
	var sendMu sync.Mutex
	var current *lease
	defer func() { cancel(); carrier.Close(); workers.Wait() }()
	stop := context.AfterFunc(ctx, func() { carrier.Close() })
	defer stop()
	for {
		raw, err := carrier.Recv(ctx)
		if err != nil {
			return roombroker.Code("seed_closed")
		}
		message, ok := decodePacket(raw)
		if !ok {
			continue
		}
		if current != nil {
			select {
			case <-current.finished:
				current = nil
			default:
			}
		}
		if message.kind == 'O' && current == nil {
			current = &lease{carrier: carrier, client: message.client, incoming: make(chan []byte, 16), done: make(chan struct{}), finished: make(chan struct{}), sendMu: &sendMu, serverSide: true}
			if _, err := rand.Read(current.server[:]); err != nil {
				return roombroker.Code("entropy_unavailable")
			}
			sendMu.Lock()
			err := carrier.SendContext(ctx, encodePacket(packet{kind: 'A', client: current.client, server: current.server}))
			sendMu.Unlock()
			if err != nil {
				return roombroker.Code("seed_closed")
			}
			current.lastAccept = time.Now()
			workers.Add(1)
			go func(session *lease) {
				defer workers.Done()
				defer close(session.finished)
				defer session.Close()
				bounded, stop := context.WithTimeout(ctx, ExchangeTimeout)
				defer stop()
				exchange(bounded, session)
			}(current)
		} else if current != nil && message.kind == 'O' && message.client == current.client && time.Since(current.lastAccept) >= 500*time.Millisecond {
			sendMu.Lock()
			err := carrier.SendContext(ctx, encodePacket(packet{kind: 'A', client: current.client, server: current.server}))
			sendMu.Unlock()
			if err != nil {
				return roombroker.Code("seed_closed")
			}
			current.lastAccept = time.Now()
		} else if current != nil && message.kind == 'C' && message.client == current.client && message.server == current.server {
			select {
			case current.incoming <- message.data:
			default:
				current.Close()
			}
		}
	}
}
