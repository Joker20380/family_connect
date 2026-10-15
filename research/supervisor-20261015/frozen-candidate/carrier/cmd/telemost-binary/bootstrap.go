package main

import (
	"context"
	"encoding/json"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func bootstrapRoom(ctx context.Context, profile, cachePath, control string, refresh bool) (roombroker.Descriptor, error) {
	raw, err := roombroker.LoadCredentials(profile)
	if err != nil {
		return roombroker.Descriptor{}, err
	}
	defer clear(raw)
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return roombroker.Descriptor{}, roombroker.Code("credentials_rejected")
	}
	cache := &bootstrap.Cache{Path: cachePath, Family: credentials.Family, Gateway: credentials.Gateway}
	event := func(name string) {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": name, "utc": time.Now().UTC()})
	}
	client, err := roombroker.NewClient(control, raw)
	if err != nil {
		return roombroker.Descriptor{}, err
	}
	if refresh {
		directory, err := client.BootstrapDirectory(ctx)
		if err != nil {
			return roombroker.Descriptor{}, err
		}
		if err := cache.Store(directory, time.Now()); err != nil {
			return roombroker.Descriptor{}, err
		}
		event("bootstrap_cache_stored")
		return roombroker.Descriptor{}, nil
	}
	if control != "https://127.0.0.1:1" {
		return roombroker.Descriptor{}, roombroker.Code("diagnostic_control_guard_required")
	}
	probe, cancel := context.WithTimeout(ctx, 2*time.Second)
	_, controlErr := client.BootstrapDirectory(probe)
	cancel()
	if controlErr != roombroker.Code("control_unavailable") {
		return roombroker.Descriptor{}, roombroker.Code("control_not_blocked")
	}
	event("bootstrap_normal_control_unavailable")
	directory, err := cache.Load(time.Now())
	if err != nil {
		return roombroker.Descriptor{}, err
	}
	event("bootstrap_cache_loaded")
	descriptor, err := bootstrap.Recover(ctx, directory, raw, event)
	if err == nil {
		event("bootstrap_closed_before_dedicated")
	}
	return descriptor, err
}
