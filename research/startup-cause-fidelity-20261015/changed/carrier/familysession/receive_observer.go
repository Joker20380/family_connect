package familysession

import "context"

type receiveObserverKey struct{}

func WatchReceive(ctx context.Context, observer func(context.Context, error)) context.Context {
	return context.WithValue(ctx, receiveObserverKey{}, observer)
}

func observeReceive(ctx context.Context, err error) {
	if observer, ok := ctx.Value(receiveObserverKey{}).(func(context.Context, error)); ok {
		observer(ctx, err)
	}
}
