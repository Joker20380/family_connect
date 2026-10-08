//go:build !fc_owner_diagnostic

package main

import "context"

func retainStartup(ctx context.Context)                {}
func startupStats(stats map[string]any, attempt int64) {}
