package worker

import (
	"context"
	"errors"
	"io"
	"net"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

const InterfaceName = "fcmesh0"
const MTU = 1280
const UnderlayMark = 64640
const TunnelIPv4 = "10.79.1.2"

var errHealth = errors.New("mesh health unavailable")

type Platform interface {
	Protect(net.Interface, int) bool
	Attach(context.Context, *wholedevice.Session) (io.Closer, error)
	Probe(context.Context) bool
}

type connection interface {
	Activate(func(context.Context, *wholedevice.Session) (io.Closer, error)) error
	State() string
	Snapshot() map[string]any
	HealthSample(time.Duration) *desktopmesh.HealthSample
	Close() error
}

type dialFunc func(context.Context, desktopmesh.Config, func(int) bool, func(string)) (connection, *startupdiag.Result, error)

type Server struct {
	mu         sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	done       chan struct{}
	routed     chan struct{}
	state      string
	reason     string
	started    bool
	lastID     uint64
	connection connection
	startup    *startupdiag.Result
	events     []string
	dropped    uint64
	platform   Platform
	dial       dialFunc
	underlying func(int) (*net.Interface, error)
	health     healthReport
	chatOwner  *restrictedchat.Owner
}

func New(parent context.Context, platform Platform) *Server {
	return NewWithOwner(parent, platform, &restrictedchat.Owner{})
}

func NewWithOwner(parent context.Context, platform Platform, owner *restrictedchat.Owner) *Server {
	ctx, cancel := context.WithCancel(parent)
	return &Server{ctx: ctx, cancel: cancel, state: "DISCONNECTED", platform: platform, underlying: net.InterfaceByIndex,
		chatOwner: owner,
		health:    healthReport{State: "off"},
		dial: func(ctx context.Context, config desktopmesh.Config, protect func(int) bool, event func(string)) (connection, *startupdiag.Result, error) {
			return desktopmesh.DialWithOwner(ctx, config, protect, event, owner)
		}}
}

func (server *Server) Handle(request Request) Reply {
	server.mu.Lock()
	defer server.mu.Unlock()
	reply := Reply{Schema: Schema, ID: request.ID, OK: true}
	if request.Schema != Schema || request.ID <= server.lastID || request.ID == 0 || (request.Start != nil && request.Action != "start") {
		request.Start.Erase()
		reply.OK, reply.Error, reply.State = false, "INVALID_COMMAND", server.state
		return reply
	}
	server.lastID = request.ID
	switch request.Action {
	case "start":
		if server.started || server.ctx.Err() != nil || !validStart(request.Start) {
			request.Start.Erase()
			reply.OK, reply.Error = false, "START_REJECTED"
			break
		}
		underlying, err := server.underlying(request.Start.UnderlyingIndex)
		if err != nil || underlying == nil || underlying.Flags&net.FlagUp == 0 || underlying.Flags&net.FlagLoopback != 0 || strings.EqualFold(underlying.Name, InterfaceName) {
			request.Start.Erase()
			reply.OK, reply.Error = false, "UNDERLAY_UNAVAILABLE"
			break
		}
		server.started, server.state = true, "CONNECTING"
		server.done, server.routed = make(chan struct{}), make(chan struct{})
		go server.connect(request.Start, *underlying)
	case "status":
	case "routed":
		if server.state != "PACKET_READY" || server.ctx.Err() != nil {
			reply.OK, reply.Error = false, "ROUTE_ACK_REJECTED"
		} else {
			server.state = "ROUTE_CONFIRMING"
			close(server.routed)
		}
	case "stop":
		server.cancel()
		if server.started {
			server.state = "STOPPING"
		} else {
			server.state = "DISCONNECTED"
		}
	default:
		request.Start.Erase()
		reply.OK, reply.Error = false, "INVALID_COMMAND"
	}
	server.snapshot(&reply)
	return reply
}

func validStart(start *Start) bool {
	if start == nil || start.Attempt <= 0 || start.BudgetMS <= 0 || start.BudgetMS > 200000 ||
		start.UnderlyingIndex <= 0 || len(start.Readiness) == 0 || len(start.Readiness) > wholedevice.MaxReadiness || len(start.Identity) != 64 || len(start.Anchor) != 32 {
		return false
	}
	if _, err := desktopmesh.Profile(start.Profile); err != nil {
		return false
	}
	host, port, err := net.SplitHostPort(start.Resolver)
	return err == nil && net.ParseIP(host).To4() != nil && port == "53"
}

func (server *Server) event(name string) {
	server.mu.Lock()
	defer server.mu.Unlock()
	if len(server.events) < 32 {
		server.events = append(server.events, name)
	} else {
		server.dropped++
	}
}

func (server *Server) connect(start *Start, underlying net.Interface) {
	defer close(server.done)
	defer start.Erase()
	config := desktopmesh.Config{Readiness: start.Readiness, Identity: start.Identity, Anchor: start.Anchor, Profile: start.Profile,
		Resolver: start.Resolver, Attempt: start.Attempt, Budget: time.Duration(start.BudgetMS) * time.Millisecond}
	core, startup, err := server.dial(server.ctx, config, func(fd int) bool { return server.platform.Protect(underlying, fd) }, server.event)
	if err == nil && core == nil {
		err = desktopmesh.ErrClosed
	}
	start.Erase()
	server.mu.Lock()
	server.startup = startup
	if err == nil {
		server.connection = core
		server.state = "TRANSPORT_READY"
	}
	server.mu.Unlock()
	if err == nil {
		defer core.Close()
		err = core.Activate(func(ctx context.Context, session *wholedevice.Session) (io.Closer, error) {
			packet, err := server.platform.Attach(ctx, session)
			if err != nil {
				return packet, err
			}
			if packet == nil {
				return nil, desktopmesh.ErrClosed
			}
			server.mu.Lock()
			if server.ctx.Err() == nil {
				server.state = "PACKET_READY"
			}
			server.mu.Unlock()
			timer := time.NewTimer(30 * time.Second)
			defer timer.Stop()
			select {
			case <-ctx.Done():
				return packet, context.Canceled
			case <-server.ctx.Done():
				return packet, context.Canceled
			case <-timer.C:
				return packet, errors.New("routing not acknowledged")
			case <-server.routed:
				return packet, nil
			}
		})
	}
	if err == nil {
		server.mu.Lock()
		if server.ctx.Err() == nil {
			server.state = "CONNECTED"
			server.health.State = "checking"
		}
		server.mu.Unlock()
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()
		started, nextHealth := time.Now(), time.Now()
		policy := new(desktopmesh.HealthPolicy)
		for err == nil {
			if !time.Now().Before(nextHealth) {
				err = server.observeHealth(core, policy, started)
				nextHealth = time.Now().Add(30 * time.Second)
				if err != nil {
					break
				}
			}
			select {
			case <-server.ctx.Done():
				err = context.Canceled
			case <-ticker.C:
				if core.State() != "CONNECTED" {
					err = io.EOF
				}
			}
		}
	}
	if core != nil {
		core.Close()
	}
	server.mu.Lock()
	defer server.mu.Unlock()
	if server.ctx.Err() != nil {
		server.state, server.reason = "DISCONNECTED", "CANCELLED"
	} else {
		server.state, server.reason = "FAILED", sessiondiag.Reason(err)
		if errors.Is(err, errHealth) {
			server.reason = "HEALTH_UNAVAILABLE"
		}
	}
}

func (server *Server) snapshot(reply *Reply) {
	reply.State = server.state
	if server.reason != "" && reply.Error == "" {
		reply.Error = server.reason
	}
	if server.state == "PACKET_READY" || server.state == "ROUTE_CONFIRMING" || server.state == "CONNECTED" {
		reply.Interface, reply.MTU = InterfaceName, MTU
	}
	reply.Snapshot = map[string]any{"startup": server.startup, "events": append([]string(nil), server.events...), "events_dropped": server.dropped, "health": server.health}
	if server.connection != nil && (server.state == "CONNECTED" || server.state == "FAILED" || server.state == "DISCONNECTED") {
		reply.Snapshot["native"] = server.connection.Snapshot()
	}
}

func (server *Server) Close() {
	server.cancel()
	server.mu.Lock()
	done := server.done
	server.mu.Unlock()
	if done != nil {
		<-done
	}
	if server.chatOwner != nil {
		server.chatOwner.Close()
	}
}

func Serve(ctx context.Context, input io.Reader, output io.Writer, platform Platform) error {
	return ServeWithOwner(ctx, input, output, platform, &restrictedchat.Owner{})
}

func ServeWithOwner(ctx context.Context, input io.Reader, output io.Writer, platform Platform, owner *restrictedchat.Owner) error {
	server := NewWithOwner(ctx, platform, owner)
	defer server.Close()
	for {
		request, err := ReadRequest(input)
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return ErrProtocol
		}
		reply := server.Handle(request)
		if request.Action == "stop" {
			server.Close()
			server.mu.Lock()
			server.snapshot(&reply)
			server.mu.Unlock()
		}
		if err := WriteReply(output, reply); err != nil {
			return err
		}
		if request.Action == "stop" {
			return nil
		}
	}
}
