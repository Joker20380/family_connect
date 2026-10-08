//go:build !fc_owner_diagnostic

package startupdiag

import "context"

func Start(ctx context.Context, attempt int64) context.Context { return ctx }
func Failure(ctx context.Context, stage string, err error)     {}
func Cancel(ctx context.Context)                               {}
func Complete(ctx context.Context, err error)                  {}
func Snapshot(ctx context.Context) *Result                     { return nil }
