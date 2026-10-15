//go:build seedacceptance && linux

package main

import (
	"context"
	"flag"
	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func seedAcceptanceOptions() func(context.Context) (context.Context, func(), error) {
	path := flag.String("research-seed-acceptance-config", "", "root-owned local seed acceptance policy; disabled by default")
	return func(ctx context.Context) (context.Context, func(), error) {
		return bootstrap.StartSeedAcceptance(ctx, *path)
	}
}
