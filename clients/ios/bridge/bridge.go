package bridge

import (
	"context"
	"encoding/binary"
	"errors"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/restrictedandroid/packet"
	"gvisor.dev/gvisor/pkg/buffer"
	"gvisor.dev/gvisor/pkg/tcpip/header"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

const MTU = 1280
const QueueSize = 64

const (
	Starting = 1
	Ready    = 2
	Failed   = 3
	Stopped  = 4
)

const (
	OK              = 0
	Invalid         = -1
	Closed          = -2
	Full            = -3
	Unsupported     = -4
	Timeout         = -5
	StartupFailed   = -6
	TransportFailed = -7
	UnderlayDenied  = -8
)

var ErrUnderlay = errors.New("iOS underlay denied")

type Opener func(context.Context) (*wholedevice.Session, error)

type Bridge struct {
	ctx      context.Context
	cancel   context.CancelFunc
	done     chan struct{}
	mu       sync.Mutex
	state    int
	failure  int
	incoming chan []byte
	endpoint *channel.Endpoint
}

func New(open Opener) *Bridge {
	ctx, cancel := context.WithCancel(context.Background())
	bridge := &Bridge{ctx: ctx, cancel: cancel, done: make(chan struct{}), state: Starting,
		incoming: make(chan []byte, QueueSize), endpoint: channel.New(QueueSize, MTU, "")}
	go bridge.run(open)
	return bridge
}

func (bridge *Bridge) fail(code int) {
	bridge.mu.Lock()
	defer bridge.mu.Unlock()
	if bridge.failure == 0 && bridge.ctx.Err() == nil {
		bridge.failure, bridge.state = code, Failed
	}
}

func (bridge *Bridge) run(open Opener) {
	defer close(bridge.done)
	defer func() {
		bridge.cancel()
		bridge.endpoint.Close()
		bridge.mu.Lock()
		defer bridge.mu.Unlock()
		for len(bridge.incoming) > 0 {
			clear(<-bridge.incoming)
		}
		if bridge.failure == 0 {
			bridge.state = Stopped
		}
	}()
	session, err := open(bridge.ctx)
	if err != nil || session == nil {
		if session != nil {
			session.Close()
		}
		code := StartupFailed
		if errors.Is(err, ErrUnderlay) {
			code = UnderlayDenied
		}
		bridge.fail(code)
		return
	}
	defer session.Close()
	if bridge.ctx.Err() != nil {
		return
	}
	engine, err := packet.Start(bridge.ctx, bridge.endpoint, session)
	if err != nil {
		bridge.fail(StartupFailed)
		return
	}
	defer func() {
		engine.Close()
		if joined, ok := engine.(interface{ Wait() }); ok {
			joined.Wait()
		}
	}()
	bridge.mu.Lock()
	if bridge.ctx.Err() == nil && !session.Failed() {
		bridge.state = Ready
	}
	bridge.mu.Unlock()
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()
	for {
		if session.Failed() {
			bridge.fail(TransportFailed)
			return
		}
		select {
		case <-bridge.ctx.Done():
			return
		case <-ticker.C:
		case data := <-bridge.incoming:
			incoming := stack.NewPacketBuffer(stack.PacketBufferOptions{Payload: buffer.MakeWithData(data)})
			bridge.endpoint.InjectInbound(header.IPv4ProtocolNumber, incoming)
			incoming.DecRef()
		}
	}
}

func (bridge *Bridge) Status() (int, int) {
	bridge.mu.Lock()
	defer bridge.mu.Unlock()
	return bridge.state, bridge.failure
}

func (bridge *Bridge) Write(data []byte, family int) int {
	if len(data) == 0 || len(data) > MTU {
		return Invalid
	}
	if family == 6 && data[0]>>4 == 6 && len(data) >= 40 {
		return Unsupported
	}
	if family != 4 || data[0]>>4 != 4 || len(data) < 20 {
		return Invalid
	}
	headerSize := int(data[0]&15) * 4
	if headerSize < 20 || headerSize > len(data) || int(binary.BigEndian.Uint16(data[2:4])) != len(data) {
		return Invalid
	}
	bridge.mu.Lock()
	defer bridge.mu.Unlock()
	if bridge.failure != 0 {
		return bridge.failure
	}
	if bridge.ctx.Err() != nil {
		return Closed
	}
	select {
	case bridge.incoming <- append([]byte(nil), data...):
		return OK
	default:
		return Full
	}
}

func (bridge *Bridge) Read(wait time.Duration) ([]byte, int, int) {
	if wait <= 0 || wait > time.Second {
		return nil, 0, Invalid
	}
	ctx, cancel := context.WithTimeout(bridge.ctx, wait)
	defer cancel()
	outgoing := bridge.endpoint.ReadContext(ctx)
	if outgoing != nil {
		defer outgoing.DecRef()
		if bridge.ctx.Err() == nil {
			view := outgoing.ToView()
			defer view.Release()
			data := append([]byte(nil), view.AsSlice()...)
			if len(data) == 0 || len(data) > MTU || data[0]>>4 != 4 {
				return nil, 0, Invalid
			}
			return data, 4, OK
		}
	}
	_, failure := bridge.Status()
	if failure != 0 {
		return nil, 0, failure
	}
	if bridge.ctx.Err() != nil {
		return nil, 0, Closed
	}
	return nil, 0, Timeout
}

func (bridge *Bridge) Cancel() { bridge.cancel() }
func (bridge *Bridge) Stop()   { bridge.cancel(); <-bridge.done }
