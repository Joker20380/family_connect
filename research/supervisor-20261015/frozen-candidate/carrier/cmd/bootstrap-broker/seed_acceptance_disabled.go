//go:build !seedacceptance || !linux

package main

import "context"

func seedAcceptanceOptions() func(context.Context) (context.Context, func(), error) {
	return func(ctx context.Context) (context.Context, func(), error) { return ctx, func() {}, nil }
}
