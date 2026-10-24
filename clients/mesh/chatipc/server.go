package chatipc

import (
	"context"
	"errors"
	"io"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type client interface {
	Route() string
	Close() error
	OpenMailbox(context.Context, time.Duration) (net.Conn, error)
	Request(context.Context, string, []byte, time.Duration) (restrictedchat.Reply, error)
}

type stream struct {
	connection       net.Conn
	lease            uint64
	cancel           context.CancelFunc
	reading, writing bool
}

func (entry *stream) close() { entry.cancel(); entry.connection.Close() }

type job struct {
	request Request
	cancel  context.CancelFunc
	client  client
	stream  *stream
}

type server struct {
	ctx                           context.Context
	cancel                        context.CancelFunc
	connection                    net.Conn
	acquire                       func(*Acquisition) (client, error)
	mu                            sync.Mutex
	writer                        sync.Mutex
	wait                          sync.WaitGroup
	leases                        map[uint64]client
	streams                       map[uint64]*stream
	jobs                          map[uint64]*job
	pendingLeases, pendingStreams int
}

func Serve(parent context.Context, connection net.Conn, owner *restrictedchat.Owner, platform worker.Platform) error {
	if parent == nil || connection == nil || owner == nil || platform == nil {
		return worker.ErrProtocol
	}
	return serve(parent, connection, func(material *Acquisition) (client, error) {
		underlying, err := net.InterfaceByIndex(material.UnderlyingIndex)
		if err != nil || underlying.Flags&net.FlagUp == 0 || underlying.Flags&net.FlagLoopback != 0 || strings.EqualFold(underlying.Name, worker.InterfaceName) {
			return nil, restrictedchat.ErrUnavailable
		}
		return owner.Acquire(restrictedchat.Config{Readiness: material.Readiness, Identity: material.Identity, Anchor: material.Anchor, Resolver: material.Resolver}, func(descriptor int) bool { return platform.Protect(*underlying, descriptor) })
	})
}

func serve(parent context.Context, connection net.Conn, acquire func(*Acquisition) (client, error)) error {
	ctx, cancel := context.WithCancel(parent)
	server := &server{ctx: ctx, cancel: cancel, connection: connection, acquire: acquire,
		leases: make(map[uint64]client), streams: make(map[uint64]*stream), jobs: make(map[uint64]*job)}
	stop := context.AfterFunc(ctx, func() { connection.Close() })
	defer stop()
	defer server.close()
	var lastID uint64
	for {
		request, err := readRequest(connection)
		if err == io.EOF || ctx.Err() != nil {
			return nil
		}
		if err != nil {
			return worker.ErrProtocol
		}
		if request.ID <= lastID {
			request.erase()
			return worker.ErrProtocol
		}
		lastID = request.ID
		server.handle(request)
	}
}

func (server *server) reply(reply Reply) {
	server.writer.Lock()
	defer server.writer.Unlock()
	defer clear(reply.Data)
	if server.ctx.Err() != nil {
		return
	}
	server.connection.SetWriteDeadline(time.Now().Add(4 * time.Second))
	if writeReply(server.connection, reply) != nil {
		server.cancel()
		server.connection.Close()
	}
}

func (server *server) handle(request Request) {
	reply := Reply{Schema: Schema, ID: request.ID, OK: true}
	server.mu.Lock()
	switch request.Action {
	case "cancel":
		if current := server.jobs[request.Target]; current != nil {
			current.cancel()
		}
	case "route":
		if current := server.leases[request.Lease]; current != nil {
			reply.Route = current.Route()
		} else {
			reply.OK, reply.Error = false, "UNAVAILABLE"
		}
	case "close":
		if current := server.streams[request.Stream]; current != nil {
			delete(server.streams, request.Stream)
			current.close()
		}
	case "release":
		if current := server.leases[request.Lease]; current != nil {
			delete(server.leases, request.Lease)
			for _, pending := range server.jobs {
				if pending.request.Lease == request.Lease || (pending.stream != nil && pending.stream.lease == request.Lease) {
					pending.cancel()
				}
			}
			for identifier, stream := range server.streams {
				if stream.lease == request.Lease {
					delete(server.streams, identifier)
					stream.close()
				}
			}
			current.Close()
		}
	default:
		if server.start(request) {
			server.mu.Unlock()
			return
		}
		reply.OK, reply.Error = false, "BUSY_OR_UNAVAILABLE"
	}
	server.mu.Unlock()
	request.erase()
	server.reply(reply)
}

func (server *server) start(request Request) bool {
	if server.ctx.Err() != nil || len(server.jobs) >= MaxJobs {
		return false
	}
	current := &job{request: request}
	switch request.Action {
	case "acquire":
		if len(server.leases)+server.pendingLeases >= restrictedchat.MaxLeases {
			return false
		}
		server.pendingLeases++
	case "open", "request":
		current.client = server.leases[request.Lease]
		if current.client == nil {
			return false
		}
		if request.Action == "open" {
			if len(server.streams)+server.pendingStreams >= MaxStreams {
				return false
			}
			server.pendingStreams++
		}
	case "read", "write", "finish":
		current.stream = server.streams[request.Stream]
		if current.stream == nil {
			return false
		}
		if request.Action == "read" {
			if current.stream.reading {
				return false
			}
			current.stream.reading = true
		} else {
			if current.stream.writing {
				return false
			}
			current.stream.writing = true
		}
	default:
		return false
	}
	ctx, cancel := context.WithTimeout(server.ctx, time.Duration(request.BudgetMS)*time.Millisecond)
	current.cancel = cancel
	server.jobs[request.ID] = current
	server.wait.Add(1)
	go server.run(ctx, current)
	return true
}

func (server *server) run(ctx context.Context, current *job) {
	defer server.wait.Done()
	request := current.request
	defer request.erase()
	defer func() { server.mu.Lock(); delete(server.jobs, request.ID); server.mu.Unlock() }()
	reply := Reply{Schema: Schema, ID: request.ID, OK: true}
	var acquired client
	var opened net.Conn
	var err error
	stopIO := func() bool { return true }
	if current.stream != nil {
		stopIO = context.AfterFunc(ctx, func() { current.stream.connection.Close() })
	}
	defer stopIO()
	switch request.Action {
	case "acquire":
		acquired, err = server.acquire(request.Acquire)
	case "open":
		opened, err = current.client.OpenMailbox(ctx, time.Duration(request.BudgetMS)*time.Millisecond)
	case "request":
		var response restrictedchat.Reply
		response, err = current.client.Request(ctx, request.Path, request.Data, time.Duration(request.BudgetMS)*time.Millisecond)
		reply.Status, reply.Data = response.Status, response.Body
	case "read":
		reply.Data = make([]byte, request.Size)
		reply.Count, err = current.stream.connection.Read(reply.Data)
		reply.Data = reply.Data[:reply.Count]
		if err == io.EOF {
			reply.EOF, err = true, nil
		}
	case "write":
		reply.Count, err = current.stream.connection.Write(request.Data)
	case "finish":
		if closer, ok := current.stream.connection.(interface{ CloseWrite() error }); ok {
			err = closer.CloseWrite()
		} else {
			err = restrictedchat.ErrUnavailable
		}
	}
	stopIO()
	server.mu.Lock()
	if ctx.Err() != nil && !errors.Is(err, restrictedchat.ErrDenied) && !errors.Is(err, restrictedchat.ErrConflict) {
		err = ctx.Err()
	}
	if request.Action == "acquire" {
		server.pendingLeases--
		if acquired == nil && err == nil {
			err = restrictedchat.ErrUnavailable
		}
		if err == nil {
			server.leases[request.ID] = acquired
			reply.Lease, reply.Route = request.ID, acquired.Route()
		} else if acquired != nil {
			acquired.Close()
		}
	}
	transferred := false
	if request.Action == "open" {
		server.pendingStreams--
		if opened == nil && err == nil {
			err = restrictedchat.ErrUnavailable
		}
		if server.leases[request.Lease] != current.client {
			err = restrictedchat.ErrUnavailable
		}
		if err == nil {
			server.streams[request.ID] = &stream{connection: opened, lease: request.Lease, cancel: current.cancel}
			reply.Stream, transferred = request.ID, true
		} else if opened != nil {
			opened.Close()
		}
	}
	if current.stream != nil {
		if request.Action == "read" {
			current.stream.reading = false
		} else {
			current.stream.writing = false
		}
		if err != nil && server.streams[request.Stream] == current.stream {
			delete(server.streams, request.Stream)
			current.stream.close()
		}
	}
	server.mu.Unlock()
	if !transferred {
		current.cancel()
	}
	if err != nil {
		reply.OK, reply.Error = false, classify(err)
		if request.Action == "request" {
			clear(reply.Data)
			reply.Data, reply.Status = nil, 0
		}
	}
	server.reply(reply)
}

func classify(err error) string {
	switch {
	case errors.Is(err, restrictedchat.ErrDenied):
		return "DENIED"
	case errors.Is(err, restrictedchat.ErrConflict):
		return "CONFLICT"
	case errors.Is(err, context.DeadlineExceeded), errors.Is(err, os.ErrDeadlineExceeded):
		return "DEADLINE"
	case errors.Is(err, context.Canceled):
		return "CANCELLED"
	default:
		return "UNAVAILABLE"
	}
}

func (server *server) close() {
	server.cancel()
	server.connection.Close()
	server.mu.Lock()
	for _, pending := range server.jobs {
		pending.cancel()
	}
	for _, current := range server.streams {
		current.close()
	}
	for _, current := range server.leases {
		current.Close()
	}
	clear(server.leases)
	clear(server.streams)
	server.mu.Unlock()
	server.wait.Wait()
}
