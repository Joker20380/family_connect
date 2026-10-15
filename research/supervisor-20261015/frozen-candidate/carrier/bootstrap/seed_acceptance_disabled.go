//go:build !seedacceptance || !linux

package bootstrap

import "context"

func acceptanceSeedContext(ctx context.Context, roomID string) context.Context { return ctx }
func (manager *SeedManager) acceptanceGeneration(*seedGeneration)              {}
