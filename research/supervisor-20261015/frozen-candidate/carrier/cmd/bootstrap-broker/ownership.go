package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func startOwnershipEvidence(broker *roombroker.Broker, path string) (func(), error) {
	if path == "" {
		return func() {}, nil
	}
	if !filepath.IsAbs(path) {
		return nil, roombroker.Code("invalid_observation")
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return nil, err
	}
	until := time.Now().Add(15 * time.Minute)
	if err := broker.CaptureOwnership(512, until); err != nil {
		file.Close()
		return nil, err
	}
	encoder := json.NewEncoder(file)
	if err := encoder.Encode(map[string]any{"schema": "admission-ownership-v1", "enabled": true, "until_ms": until.UnixMilli(), "event_limit": 512, "pid": os.Getpid(), "invocation": os.Getenv("INVOCATION_ID")}); err != nil {
		file.Close()
		return nil, err
	}
	stop, done := make(chan struct{}), make(chan struct{})
	var once sync.Once
	go func() {
		defer close(done)
		defer file.Close()
		ticker := time.NewTicker(250 * time.Millisecond)
		defer ticker.Stop()
		timer := time.NewTimer(time.Until(until))
		defer timer.Stop()
		written := 0
		flush := func() error {
			snapshot := broker.OwnershipSnapshot()
			for _, event := range snapshot.Events[written:] {
				if err := encoder.Encode(event); err != nil {
					return err
				}
				written++
			}
			return nil
		}
		for {
			select {
			case <-stop:
			case <-timer.C:
			case <-ticker.C:
				if flush() != nil {
					return
				}
				continue
			}
			if flush() == nil {
				_ = encoder.Encode(map[string]any{"schema": "admission-ownership-v1", "stopped": true, "limited": broker.OwnershipSnapshot().Limited, "written": written})
			}
			return
		}
	}()
	return func() { once.Do(func() { close(stop) }); <-done }, nil
}
