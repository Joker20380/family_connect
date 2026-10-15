package wholedevice

import (
	"context"
	"errors"
	"sync"

	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

func AttachMux(ctx context.Context, mux *tcpforward.Mux, closeCarrier func()) *Session {
	return Attach(ctx, muxPlane{mux}, closeCarrier)
}

func (session *Session) OpenService(ctx context.Context, name string) (Stream, error) {
	if name != "chat-mailbox" && name != "chat-api" {
		return nil, errors.New("service_denied")
	}
	if session.Failed() {
		return nil, ErrClosed
	}
	select {
	case session.serviceSlots <- struct{}{}:
	default:
		return nil, errors.New("service_busy")
	}
	bounded, cancel := context.WithCancel(ctx)
	stop := context.AfterFunc(session.ctx, cancel)
	release := func() { stop(); cancel(); <-session.serviceSlots }
	stream, err := session.plane.Open(bounded, name+".family-connect.invalid", 1)
	if err != nil {
		release()
		return nil, err
	}
	return &serviceStream{Stream: stream, release: release}, nil
}

type serviceStream struct {
	Stream
	once    sync.Once
	release func()
}

func (stream *serviceStream) Close() error {
	err := stream.Stream.Close()
	stream.once.Do(stream.release)
	return err
}

func (stream *serviceStream) Reset() error {
	err := stream.Stream.Reset()
	stream.once.Do(stream.release)
	return err
}
