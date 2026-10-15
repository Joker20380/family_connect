package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

var peerTag = regexp.MustCompile(`^[0-9a-f]{64}$`)

type peerEvidenceSlot struct {
	tag     string
	first   atomic.Pointer[sessiontrace.Event]
	close   atomic.Pointer[sessiontrace.Event]
	lease   atomic.Pointer[sessiontrace.Event]
	dropped atomic.Uint64
}

type peerEvidenceSelection struct{ slots []*peerEvidenceSlot }

type peerEvidenceSnapshot struct {
	Schema       int                  `json:"schema"`
	SessionTag   string               `json:"session_tag"`
	Endpoint     string               `json:"endpoint"`
	Events       []sessiontrace.Event `json:"events"`
	FirstFailure *sessiontrace.Event  `json:"first_failure,omitempty"`
	Dropped      uint64               `json:"collector_dropped"`
	Evicted      uint64               `json:"history_evicted"`
	FirstClose   *sessiontrace.Event  `json:"first_close,omitempty"`
	Lease        *sessiontrace.Event  `json:"lease,omitempty"`
}

type startupEvidence struct {
	UTC    int64  `json:"utc_ms"`
	Event  string `json:"event"`
	Stage  string `json:"stage,omitempty"`
	Reason string `json:"reason,omitempty"`
}

func safeStartup(event, stage, reason string) (startupEvidence, bool) {
	switch event {
	case "bootstrap_seed_ready", "bootstrap_family_open", "bootstrap_family_auth", "bootstrap_handoff", "bootstrap_exchange_failed", "bootstrap_exchange_rejected":
	default:
		return startupEvidence{}, false
	}
	switch stage {
	case "", "profile", "family_open", "challenge", "hello_send", "request_receive", "create", "claim", "ready_send", "bye_receive", "descriptor_expiry", "authorize", "bye_send":
	default:
		stage = "unknown"
	}
	switch reason {
	case "", "unauthorized", "device_busy", "outstanding_limit", "closed", "entropy_unavailable", "bootstrap_protocol_rejected", "descriptor_expired", "authorization_changed", "cancelled", "stale_or_unbound_setup", "setup_replayed", "descriptor_replayed", "provider_failure", "provider_response", "provider_cancelled", "provider_timeout", "provider_transport", "provider_request", "provider_bad_request", "provider_unauthorized", "provider_forbidden", "provider_rate_limited", "provider_unavailable", "provider_status", "provider_body", "provider_json", "provider_id", "provider_join_url", "gateway_failed", "gateway_ready_timeout", "context_cancelled", "context_deadline", "unknown":
	default:
		reason = "unknown"
	}
	return startupEvidence{time.Now().UnixMilli(), event, stage, reason}, true
}

func newPeerEvidence(directory string) (func(sessiontrace.Event), func(string, string, string), func(), error) {
	if directory == "" {
		return func(sessiontrace.Event) {}, func(string, string, string) {}, func() {}, nil
	}
	info, err := os.Lstat(directory)
	if err != nil || !filepath.IsAbs(directory) || info.Mode()&os.ModeSymlink != 0 || !info.IsDir() || info.Mode().Perm() != 0700 {
		return nil, nil, nil, errors.New("research evidence directory rejected")
	}
	return startPeerEvidence(directory, time.Second, 20*time.Minute)
}

func startPeerEvidence(directory string, interval, lifetime time.Duration) (func(sessiontrace.Event), func(string, string, string), func(), error) {
	queue := make(chan sessiontrace.Event, 16)
	startupQueue := make(chan startupEvidence, 16)
	var startupFirst atomic.Pointer[startupEvidence]
	var startupDropped atomic.Uint64
	stop, done := make(chan struct{}), make(chan struct{})
	var selection atomic.Pointer[peerEvidenceSelection]
	selection.Store(&peerEvidenceSelection{})
	var closed atomic.Bool
	var once sync.Once
	startupSink := func(event, stage, reason string) {
		if closed.Load() {
			return
		}
		value, allowed := safeStartup(event, stage, reason)
		if !allowed {
			return
		}
		if event == "bootstrap_exchange_rejected" || event == "bootstrap_exchange_failed" {
			startupFirst.CompareAndSwap(nil, &value)
		}
		select {
		case startupQueue <- value:
		default:
			startupDropped.Add(1)
		}
	}
	sink := func(event sessiontrace.Event) {
		if closed.Load() {
			return
		}
		for _, slot := range selection.Load().slots {
			if event.SessionTag != slot.tag {
				continue
			}
			if event.CloseSource != "" {
				value := event
				slot.close.CompareAndSwap(nil, &value)
			}
			if event.LeaseDeadlineMS != 0 {
				value := event
				slot.lease.CompareAndSwap(nil, &value)
			}
			if event.State == "FAILED" && event.Reason != "NONE" {
				copy := event
				slot.first.CompareAndSwap(nil, &copy)
			}
			select {
			case queue <- event:
			default:
				slot.dropped.Add(1)
			}
			return
		}
	}
	go func() {
		defer close(done)
		defer closed.Store(true)
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		deadline := time.NewTimer(lifetime)
		defer deadline.Stop()
		history := map[string][]sessiontrace.Event{}
		startupHistory := []startupEvidence{}
		var startupEvicted uint64
		startupWritten := false
		evicted := map[string]uint64{}
		written := map[string]bool{}
		expires := time.Now().Add(lifetime).UnixMilli()
		writeStatus := func(stopped bool) {
			status, _ := json.Marshal(map[string]any{"schema": 1, "utc_ms": time.Now().UnixMilli(), "expires_ms": expires, "selected_sessions": len(selection.Load().slots), "stopped": stopped})
			if file, err := os.OpenFile(filepath.Join(directory, "status.tmp"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600); err == nil {
				_, writeErr := file.Write(status)
				closeErr := file.Close()
				if writeErr == nil && closeErr == nil {
					_ = os.Rename(filepath.Join(directory, "status.tmp"), filepath.Join(directory, "status.json"))
				}
			}
		}
		defer writeStatus(true)
		refresh := func() {
			path := filepath.Join(directory, "allow-tags")
			info, err := os.Lstat(path)
			if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || info.Size() > 130 {
				return
			}
			data, err := os.ReadFile(path)
			if err != nil {
				return
			}
			tags := strings.Fields(string(data))
			if len(tags) > 2 {
				return
			}
			current := selection.Load()
			next := &peerEvidenceSelection{slots: append([]*peerEvidenceSlot(nil), current.slots...)}
			for _, tag := range tags {
				if !peerTag.MatchString(tag) {
					return
				}
				found := false
				for _, slot := range next.slots {
					if slot.tag == tag {
						found = true
					}
				}
				if !found {
					next.slots = append(next.slots, &peerEvidenceSlot{tag: tag})
				}
			}
			if len(next.slots) <= 2 {
				selection.Store(next)
			}
		}
		flush := func() {
			if len(startupHistory) > 0 || startupFirst.Load() != nil {
				data, marshalErr := json.Marshal(map[string]any{"schema": 1, "scope": "gateway_invocation_not_client_identity", "events": startupHistory, "first_failure": startupFirst.Load(), "collector_dropped": startupDropped.Load(), "history_evicted": startupEvicted})
				if marshalErr == nil && len(data) <= 16384 {
					if startupFirst.Load() != nil && !startupWritten {
						if file, openErr := os.OpenFile(filepath.Join(directory, "startup.first.json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600); openErr == nil {
							_, writeErr := file.Write(data)
							closeErr := file.Close()
							startupWritten = writeErr == nil && closeErr == nil
						}
					}
					if file, openErr := os.OpenFile(filepath.Join(directory, "startup.tmp"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600); openErr == nil {
						_, writeErr := file.Write(data)
						closeErr := file.Close()
						if writeErr == nil && closeErr == nil {
							_ = os.Rename(filepath.Join(directory, "startup.tmp"), filepath.Join(directory, "startup.latest.json"))
						}
					}
				}
			}
			for _, slot := range selection.Load().slots {
				events := history[slot.tag]
				first := slot.first.Load()
				if len(events) == 0 && first == nil {
					continue
				}
				value := peerEvidenceSnapshot{1, slot.tag, "gateway", events, first, slot.dropped.Load(), evicted[slot.tag], slot.close.Load(), slot.lease.Load()}
				data, err := json.Marshal(value)
				if err != nil || len(data) > 1024*1024 {
					continue
				}
				if (first != nil || slot.close.Load() != nil) && !written[slot.tag] {
					file, err := os.OpenFile(filepath.Join(directory, slot.tag+".first.json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
					if err == nil {
						_, err = file.Write(data)
						closeErr := file.Close()
						written[slot.tag] = err == nil && closeErr == nil
					}
				}
				temporary := filepath.Join(directory, slot.tag+".tmp")
				file, err := os.OpenFile(temporary, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
				if err != nil {
					continue
				}
				_, err = file.Write(data)
				closeErr := file.Close()
				if err == nil && closeErr == nil {
					_ = os.Rename(temporary, filepath.Join(directory, slot.tag+".latest.json"))
				}
			}
		}
		defer flush()
		for {
			select {
			case <-stop:
				return
			case <-deadline.C:
				return
			case <-ticker.C:
				if info, err := os.Lstat(filepath.Join(directory, "stop-request")); err == nil && info.Mode().IsRegular() && info.Mode().Perm() == 0600 && info.Size() == 0 {
					return
				}
				refresh()
				flush()
				writeStatus(false)
			case event := <-queue:
				events := history[event.SessionTag]
				if len(events) == 32 {
					evicted[event.SessionTag]++
					copy(events, events[1:])
					events = events[:31]
				}
				history[event.SessionTag] = append(events, event)
			case event := <-startupQueue:
				if len(startupHistory) == 16 {
					startupEvicted++
					copy(startupHistory, startupHistory[1:])
					startupHistory = startupHistory[:15]
				}
				startupHistory = append(startupHistory, event)
			}
		}
	}()
	return sink, startupSink, func() { once.Do(func() { closed.Store(true); close(stop) }); <-done }, nil
}
