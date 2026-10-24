package automatic

import (
	"context"
	"crypto/rand"
	"errors"
	"io"
	"math/big"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopauto"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

const CleanupTimeout = 20 * time.Second

type pendingCall struct {
	identifier uint64
	operation  string
	reply      chan HostReply
	delivered  bool
}

type remoteHost struct {
	ctx        context.Context
	cancel     context.CancelFunc
	started    time.Time
	writer     io.WriteCloser
	writeMu    sync.Mutex
	mu         sync.Mutex
	pending    *pendingCall
	identifier uint64
	generation atomic.Uint64
	network    atomic.Bool
	drain      time.Duration
	begin      chan struct{}
}

func (host *remoteHost) send(field string, value any) error {
	host.writeMu.Lock()
	defer host.writeMu.Unlock()
	if host.ctx.Err() != nil {
		return host.ctx.Err()
	}
	if err := encoded(host.writer, field, value); err != nil {
		host.cancel()
		return err
	}
	return nil
}

func (host *remoteHost) Now() time.Duration { return time.Since(host.started) }

func (host *remoteHost) Jitter(maximum time.Duration) time.Duration {
	value, err := rand.Int(rand.Reader, big.NewInt(int64(maximum)+1))
	if err != nil {
		return 0
	}
	return time.Duration(value.Int64())
}

func (host *remoteHost) NetworkAvailable() bool { return host.network.Load() }

func (host *remoteHost) Pause(ctx context.Context, delay time.Duration) error {
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-host.ctx.Done():
		return host.ctx.Err()
	case <-timer.C:
		return nil
	}
}

func (host *remoteHost) receive(reply HostReply) error {
	host.mu.Lock()
	defer host.mu.Unlock()
	call := host.pending
	if call == nil || call.delivered || call.identifier != reply.ID || (call.operation != "configure" && len(reply.Candidates) != 0) {
		return worker.ErrProtocol
	}
	select {
	case call.reply <- reply:
		call.delivered = true
		return nil
	default:
		return worker.ErrProtocol
	}
}

func (host *remoteHost) call(ctx context.Context, operation string, candidate desktopauto.Candidate) (HostReply, error) {
	deadline, ok := ctx.Deadline()
	if !ok || ctx.Err() != nil || host.ctx.Err() != nil {
		return HostReply{}, context.Canceled
	}
	host.mu.Lock()
	if host.pending != nil || host.identifier >= maxIdentifier {
		host.mu.Unlock()
		return HostReply{}, desktopauto.Rejected{Category: desktopauto.Internal}
	}
	host.identifier++
	call := &pendingCall{identifier: host.identifier, operation: operation, reply: make(chan HostReply, 1)}
	host.pending = call
	host.mu.Unlock()
	defer func() {
		host.mu.Lock()
		host.pending = nil
		host.mu.Unlock()
	}()
	request := HostCall{Schema: Schema, ID: call.identifier, Operation: operation, Candidate: candidate,
		BudgetMS: max(1, time.Until(deadline).Milliseconds()), Generation: host.generation.Load()}
	if err := host.send("host_call", request); err != nil {
		return HostReply{}, err
	}
	var reply HostReply
	select {
	case reply = <-call.reply:
	case <-host.ctx.Done():
		return HostReply{}, host.ctx.Err()
	case <-ctx.Done():
		if err := host.send("host_cancel", HostCancel{Schema: Schema, ID: call.identifier}); err != nil {
			return HostReply{}, err
		}
		timer := time.NewTimer(host.drain)
		defer timer.Stop()
		select {
		case <-call.reply:
			return HostReply{}, ctx.Err()
		case <-host.ctx.Done():
			return HostReply{}, host.ctx.Err()
		case <-timer.C:
			host.cancel()
			return HostReply{}, desktopauto.Rejected{Category: desktopauto.Internal}
		}
	}
	if err := ctx.Err(); err != nil {
		return HostReply{}, err
	}
	if !*reply.OK {
		return HostReply{}, desktopauto.Rejected{Category: reply.Failure, TemporaryBootstrap: reply.TemporaryBootstrap}
	}
	return reply, nil
}

func (host *remoteHost) Configure(ctx context.Context, _ time.Duration) ([]desktopauto.Candidate, error) {
	host.begun()
	reply, err := host.call(ctx, "configure", "")
	return reply.Candidates, err
}

func (host *remoteHost) begun() {
	host.mu.Lock()
	defer host.mu.Unlock()
	if host.begin != nil {
		close(host.begin)
		host.begin = nil
	}
}

func (host *remoteHost) Open(ctx context.Context, candidate desktopauto.Candidate, _ time.Duration) error {
	_, err := host.call(ctx, "open", candidate)
	return err
}

func (host *remoteHost) CloseCandidate(ctx context.Context) error {
	_, err := host.call(ctx, "close", "")
	return err
}

func (host *remoteHost) Release(ctx context.Context) error {
	_, err := host.call(ctx, "release", "")
	return err
}

func (host *remoteHost) Remember(candidate desktopauto.Candidate) error {
	ctx, cancel := context.WithTimeout(host.ctx, CleanupTimeout)
	defer cancel()
	_, err := host.call(ctx, "remember", candidate)
	return err
}

func replyError(err error) string {
	switch {
	case err == nil:
		return ""
	case errors.Is(err, desktopauto.ErrBusy):
		return "BUSY"
	case errors.Is(err, desktopauto.ErrStale):
		return "STALE"
	case errors.Is(err, desktopauto.ErrInvalid):
		return "INVALID"
	default:
		return "INTERNAL"
	}
}

func Serve(ctx context.Context, input io.ReadCloser, output io.WriteCloser) error {
	return serve(ctx, input, output, CleanupTimeout)
}

func serve(parent context.Context, input io.ReadCloser, output io.WriteCloser, drain time.Duration) error {
	ctx, cancel := context.WithCancel(parent)
	host := &remoteHost{ctx: ctx, cancel: cancel, started: time.Now(), writer: output, drain: drain}
	controller, err := desktopauto.New(host, CleanupTimeout)
	if err != nil {
		cancel()
		return err
	}
	closed := make(chan struct{})
	go func() {
		<-ctx.Done()
		input.Close()
		output.Close()
		close(closed)
	}()
	var operation sync.WaitGroup
	var busy atomic.Bool
	var disconnect atomic.Bool
	var lastCommand uint64
	defer func() {
		cancel()
		operation.Wait()
		<-closed
	}()
	result := func(command Command, failure error) Reply {
		return Reply{Schema: Schema, ID: command.ID, OK: failure == nil,
			Error: replyError(failure), Snapshot: controller.Snapshot()}
	}
	reply := func(command Command, failure error) {
		host.send("reply", result(command, failure))
	}
	for ctx.Err() == nil {
		frame, failure := read(input)
		if failure != nil {
			return failure
		}
		if frame.Host != nil {
			if host.receive(*frame.Host) != nil {
				return worker.ErrProtocol
			}
			continue
		}
		command := *frame.Command
		if command.ID <= lastCommand {
			return worker.ErrProtocol
		}
		lastCommand = command.ID
		if command.Action == "status" {
			reply(command, nil)
			continue
		}
		if command.Action != "connect" && command.Generation != host.generation.Load() {
			reply(command, desktopauto.ErrStale)
			continue
		}
		if command.Action == "network" {
			host.network.Store(*command.Network)
			reply(command, nil)
			continue
		}
		if command.Action == "disconnect" {
			if !disconnect.CompareAndSwap(false, true) {
				reply(command, desktopauto.ErrBusy)
				continue
			}
			if controller.Interrupt(command.Generation, desktopauto.Cancelled) != nil {
				disconnect.Store(false)
				reply(command, desktopauto.ErrStale)
				continue
			}
			operation.Add(1)
			go func() {
				defer operation.Done()
				failure := controller.Disconnect(command.Generation)
				response := result(command, failure)
				disconnect.Store(false)
				host.send("reply", response)
			}()
			continue
		}
		if disconnect.Load() || !busy.CompareAndSwap(false, true) {
			reply(command, desktopauto.ErrBusy)
			continue
		}
		var beginning chan struct{}
		if command.Action == "connect" {
			if command.Generation <= host.generation.Load() {
				busy.Store(false)
				reply(command, desktopauto.ErrStale)
				continue
			}
			if controller.Snapshot().State != desktopauto.Disconnected {
				busy.Store(false)
				reply(command, desktopauto.ErrBusy)
				continue
			}
			host.generation.Store(command.Generation)
			host.network.Store(*command.Network)
			beginning = make(chan struct{})
			host.mu.Lock()
			host.begin = beginning
			host.mu.Unlock()
		}
		operation.Add(1)
		go func() {
			defer operation.Done()
			var failure error
			switch command.Action {
			case "connect":
				failure = controller.Connect(ctx, command.Generation, command.Preferred, command.LastGood)
				host.begun()
			case "retry":
				failure = controller.Retry(command.Generation)
			case "lost":
				failure = controller.Lost(command.Generation, command.Reason)
			case "healthy":
				failure = controller.Healthy(command.Generation, *command.Healthy)
			}
			response := result(command, failure)
			busy.Store(false)
			host.send("reply", response)
		}()
		if beginning != nil {
			select {
			case <-beginning:
			case <-ctx.Done():
				return ctx.Err()
			}
		}
	}
	return ctx.Err()
}
