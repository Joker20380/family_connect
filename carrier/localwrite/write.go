package localwrite

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
)

type key struct{}

type Write struct {
	ctx        context.Context
	obsolete   <-chan struct{}
	registered atomic.Bool
	state      atomic.Uint32
	remaining  atomic.Int32
	done       chan error
	once       sync.Once
}

func Observe(ctx context.Context, obsolete <-chan struct{}) (context.Context, *Write) {
	write := &Write{ctx: ctx, obsolete: obsolete, done: make(chan error, 1)}
	return context.WithValue(ctx, key{}, write), write
}

func Register(ctx context.Context, fragments int) (*Write, error) {
	write, _ := ctx.Value(key{}).(*Write)
	if write == nil {
		return nil, nil
	}
	if fragments < 1 || !write.registered.CompareAndSwap(false, true) {
		return nil, errors.New("local write: repeated registration")
	}
	write.remaining.Store(int32(fragments))
	return write, nil
}

func (write *Write) finish(err error) { write.once.Do(func() { write.done <- err }) }

func (write *Write) Begin() bool {
	if write == nil {
		return true
	}
	if write.state.Load() == 0 {
		select {
		case <-write.obsolete:
			if write.state.CompareAndSwap(0, 2) {
				write.finish(nil)
			}
		case <-write.ctx.Done():
			if write.state.CompareAndSwap(0, 2) {
				write.finish(write.ctx.Err())
			}
		default:
			write.state.CompareAndSwap(0, 1)
		}
	}
	return write.state.Load() == 1
}

func (write *Write) Complete(err error) {
	if write == nil {
		return
	}
	if err != nil {
		write.finish(err)
		return
	}
	if write.remaining.Add(-1) == 0 {
		write.finish(nil)
	}
}

func (write *Write) Wait() error {
	if !write.registered.Load() {
		return nil
	}
	select {
	case err := <-write.done:
		return err
	case <-write.ctx.Done():
		write.state.CompareAndSwap(0, 2)
		return write.ctx.Err()
	case <-write.obsolete:
		if write.state.CompareAndSwap(0, 2) {
			return nil
		}
		select {
		case err := <-write.done:
			return err
		case <-write.ctx.Done():
			return write.ctx.Err()
		}
	}
}
