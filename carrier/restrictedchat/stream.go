package restrictedchat

import (
	"context"
	"net"
	"os"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type streamConn struct {
	ctx        context.Context
	stream     wholedevice.Stream
	release    func()
	mu         sync.Mutex
	closed     bool
	expired    bool
	stop       func() bool
	readTimer  *time.Timer
	writeTimer *time.Timer
}

func newStreamConn(ctx context.Context, stream wholedevice.Stream, release func()) *streamConn {
	connection := &streamConn{ctx: ctx, stream: stream, release: release}
	connection.mu.Lock()
	connection.stop = context.AfterFunc(ctx, func() { connection.Close() })
	connection.mu.Unlock()
	return connection
}

func (connection *streamConn) Read(buffer []byte) (int, error) {
	count, err := connection.stream.Read(buffer)
	return count, connection.failure(err)
}

func (connection *streamConn) Write(buffer []byte) (int, error) {
	count, err := connection.stream.Write(buffer)
	return count, connection.failure(err)
}

func (connection *streamConn) failure(err error) error {
	if err == nil {
		return nil
	}
	connection.mu.Lock()
	expired := connection.expired
	connection.mu.Unlock()
	if expired {
		return os.ErrDeadlineExceeded
	}
	if connection.ctx.Err() != nil {
		return connection.ctx.Err()
	}
	return err
}

func (connection *streamConn) CloseWrite() error { return connection.stream.CloseWrite() }

func (connection *streamConn) Close() error {
	connection.mu.Lock()
	if connection.closed {
		connection.mu.Unlock()
		return nil
	}
	connection.closed = true
	connection.stop()
	for _, timer := range []*time.Timer{connection.readTimer, connection.writeTimer} {
		if timer != nil {
			timer.Stop()
		}
	}
	connection.mu.Unlock()
	defer connection.release()
	return connection.stream.Reset()
}

func (connection *streamConn) LocalAddr() net.Addr {
	return &net.UnixAddr{Name: "chat-service", Net: "unix"}
}

func (connection *streamConn) RemoteAddr() net.Addr { return connection.LocalAddr() }

func (connection *streamConn) timer(previous **time.Timer, deadline time.Time) {
	if *previous != nil {
		(*previous).Stop()
		*previous = nil
	}
	if !deadline.IsZero() {
		var timer *time.Timer
		timer = time.AfterFunc(time.Until(deadline), func() {
			connection.mu.Lock()
			if connection.closed || *previous != timer {
				connection.mu.Unlock()
				return
			}
			connection.expired = true
			connection.mu.Unlock()
			connection.Close()
		})
		*previous = timer
	}
}

func (connection *streamConn) SetDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if connection.closed {
		return net.ErrClosed
	}
	connection.timer(&connection.readTimer, deadline)
	connection.timer(&connection.writeTimer, deadline)
	return nil
}

func (connection *streamConn) SetReadDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if connection.closed {
		return net.ErrClosed
	}
	connection.timer(&connection.readTimer, deadline)
	return nil
}

func (connection *streamConn) SetWriteDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if connection.closed {
		return net.ErrClosed
	}
	connection.timer(&connection.writeTimer, deadline)
	return nil
}
