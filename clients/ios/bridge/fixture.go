package bridge

import (
	"context"
	"sync"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type Fixture struct {
	done chan struct{}
	once sync.Once
}

func NewFixture() *Fixture { return &Fixture{done: make(chan struct{})} }
func (fixture *Fixture) Open(context.Context, string, uint16) (wholedevice.Stream, error) {
	return nil, wholedevice.ErrClosed
}
func (fixture *Fixture) QueryDNS(ctx context.Context, query []byte) ([]byte, error) {
	if len(query) < 12 {
		return nil, wholedevice.ErrClosed
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	answer := append([]byte(nil), query...)
	answer[2] |= 0x80
	return answer, nil
}
func (fixture *Fixture) Close() error { fixture.once.Do(func() { close(fixture.done) }); return nil }
func (fixture *Fixture) Wait() error  { <-fixture.done; return wholedevice.ErrClosed }
func (fixture *Fixture) Attach(ctx context.Context) (*wholedevice.Session, error) {
	return wholedevice.Attach(ctx, fixture, nil), nil
}
