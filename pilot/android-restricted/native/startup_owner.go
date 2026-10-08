//go:build fc_owner_diagnostic

package main

import (
	"context"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
)

var lastStartup context.Context

func retainStartup(ctx context.Context) { lastStartup = ctx }

func startupStats(stats map[string]any, attempt int64) {
	if lastStartup == nil {
		return
	}
	result := startupdiag.Snapshot(lastStartup)
	if result != nil && result.Attempt == attempt {
		stats["owner_startup"] = result
	}
}
