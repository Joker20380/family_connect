//go:build android

package main

// #include <stdint.h>
// int fcRestrictedProtect(uintptr_t owner, int fd);
// void fcRestrictedRelease(uintptr_t owner);
import "C"

import (
	"context"
	"encoding/json"
	"errors"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/restrictedandroid/packet"
	"github.com/xtls/xray-core/proxy/tun"
	"golang.org/x/sys/unix"
	"gvisor.dev/gvisor/pkg/tcpip/link/fdbased"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

var ownerMu sync.Mutex
var current *ownedSession
var sequence int64

type ownedSession struct {
	id       int64
	owner    C.uintptr_t
	ctx      context.Context
	cancel   context.CancelFunc
	done     chan struct{}
	mu       sync.Mutex
	state    int
	events   []string
	network  *underlay.Network
	session  *wholedevice.Session
	engine   tun.Stack
	endpoint stack.LinkEndpoint
	fd       int
}

func (owned *ownedSession) event(name string) {
	owned.mu.Lock()
	defer owned.mu.Unlock()
	if len(owned.events) < 32 {
		owned.events = append(owned.events, name)
	}
}

func (owned *ownedSession) failure(err error) {
	if err == nil {
		return
	}
	switch err {
	case roombroker.Code("credentials_rejected"):
		owned.event("startup_credentials_rejected")
	case roombroker.Code("control_unavailable"):
		owned.event("startup_control_unavailable")
	default:
		owned.event("startup_failed")
	}
}

//export fcRestrictedBegin
func fcRestrictedBegin(directory, control, resolver string, owner C.uintptr_t) int64 {
	return begin(directory, control, resolver, nil, nil, owner)
}

//export fcRestrictedValidationCode
func fcRestrictedValidationCode(response, public, anchor string) int32 {
	return wholedevice.DeliveryValidationCode([]byte(response), []byte(public), []byte(anchor), time.Now())
}

//export fcRestrictedValidateDelivery
func fcRestrictedValidateDelivery(response, public, anchor string) int32 {
	_, _, err := wholedevice.ValidateDelivery([]byte(response), []byte(public), []byte(anchor), time.Now())
	if err != nil {
		return 0
	}
	return 1
}

//export fcRestrictedBeginReady
func fcRestrictedBeginReady(response, identity, anchor, resolver string, owner C.uintptr_t) int64 {
	material := []byte(identity)
	defer clear(material)
	profile, directory, err := wholedevice.DeliveryMaterial([]byte(response), material, []byte(anchor), time.Now())
	if err != nil {
		C.fcRestrictedRelease(owner)
		return 0
	}
	return begin("/", "provisioned", resolver, profile, directory, owner)
}

func begin(directory, control, resolver string, profile, seed []byte, owner C.uintptr_t) int64 {
	directory, control, resolver = strings.Clone(directory), strings.Clone(control), strings.Clone(resolver)
	ownerMu.Lock()
	defer ownerMu.Unlock()
	if current != nil || !filepath.IsAbs(directory) {
		clear(profile)
		C.fcRestrictedRelease(owner)
		return 0
	}
	ctx, cancel := context.WithCancel(context.Background())
	network, err := underlay.New(ctx, resolver, func(fd int) bool { return C.fcRestrictedProtect(owner, C.int(fd)) != 0 })
	if err != nil {
		clear(profile)
		cancel()
		C.fcRestrictedRelease(owner)
		return 0
	}
	sequence++
	owned := &ownedSession{id: sequence, owner: owner, ctx: ctx, cancel: cancel, done: make(chan struct{}), network: network, fd: -1}
	current = owned
	go func() {
		defer clear(profile)
		defer close(owned.done)
		var err error
		path, cache := filepath.Join(directory, "family.json"), filepath.Join(directory, "bootstrap.json")
		if control != "" && control != "auto" && control != "provisioned" {
			bounded, finish := context.WithTimeout(ctx, 30*time.Second)
			defer finish()
			err = wholedevice.Refresh(bounded, path, cache, control, network)
			owned.failure(err)
			if err == nil {
				owned.event("bootstrap_cache_stored")
			}
			owned.mu.Lock()
			defer owned.mu.Unlock()
			if err == nil {
				owned.state = 4
			} else {
				owned.state = 3
			}
			return
		}
		var session *wholedevice.Session
		if control == "provisioned" {
			session, err = wholedevice.OpenProvisioned(ctx, profile, seed, network, owned.event)
		} else if control == "auto" {
			session, err = wholedevice.OpenCached(ctx, path, cache, network, owned.event)
		} else {
			session, err = wholedevice.Open(ctx, path, cache, network, owned.event)
		}
		owned.failure(err)
		owned.mu.Lock()
		defer owned.mu.Unlock()
		if err != nil {
			owned.state = 3
			if errors.Is(err, familysession.ErrRejected) || errors.Is(err, roombroker.Code("credentials_rejected")) || errors.Is(err, roombroker.Code("bootstrap_auth_failed")) {
				owned.state = 5
			}
			return
		}
		owned.session = session
		owned.state = 1
	}()
	return owned.id
}

//export fcRestrictedTun
func fcRestrictedTun(id int64, tunFD int32) int32 {
	ownerMu.Lock()
	defer ownerMu.Unlock()
	if current == nil || current.id != id {
		return 0
	}
	owned := current
	owned.mu.Lock()
	defer owned.mu.Unlock()
	if owned.state != 1 || owned.session.Failed() || owned.engine != nil || tunFD < 3 {
		return 0
	}
	fd, err := unix.Dup(int(tunFD))
	if err != nil {
		return 0
	}
	unix.CloseOnExec(fd)
	if unix.SetNonblock(fd, true) != nil {
		unix.Close(fd)
		return 0
	}
	endpoint, err := fdbased.New(&fdbased.Options{FDs: []int{fd}, MTU: 1280, RXChecksumOffload: true})
	if err != nil {
		unix.Close(fd)
		return 0
	}
	engine, err := packet.Start(owned.ctx, endpoint, owned.session)
	if err != nil {
		endpoint.Close()
		unix.Close(fd)
		return 0
	}
	owned.fd, owned.engine, owned.endpoint, owned.state = fd, engine, endpoint, 2
	owned.events = append(owned.events, "vpn_packet_ready")
	return 1
}

//export fcRestrictedState
func fcRestrictedState(id int64) int32 {
	ownerMu.Lock()
	defer ownerMu.Unlock()
	if current == nil || current.id != id {
		return -1
	}
	current.mu.Lock()
	defer current.mu.Unlock()
	if current.session != nil && current.session.Failed() {
		current.state = 3
	}
	return int32(current.state)
}

//export fcRestrictedStats
func fcRestrictedStats(id int64) *C.char {
	ownerMu.Lock()
	defer ownerMu.Unlock()
	if current == nil || current.id != id {
		return C.CString("{}")
	}
	owned := current
	owned.mu.Lock()
	defer owned.mu.Unlock()
	var memory runtime.MemStats
	runtime.ReadMemStats(&memory)
	stats := map[string]any{"events": owned.events, "state": owned.state, "goroutines": runtime.NumGoroutine(),
		"go_heap": memory.Alloc, "protect_ok": owned.network.Protected.Load(), "protect_denied": owned.network.Rejected.Load(), "underlay_dns": owned.network.DNS.Load()}
	owned.events = nil
	if owned.session != nil {
		stats["packet"] = owned.session.Snapshot()
	}
	raw, _ := json.Marshal(stats)
	return C.CString(string(raw))
}

//export fcRestrictedStop
func fcRestrictedStop(id int64) int32 {
	ownerMu.Lock()
	defer ownerMu.Unlock()
	if current == nil {
		return 1
	}
	if current.id != id {
		return 0
	}
	owned := current
	owned.cancel()
	<-owned.done
	if owned.session != nil {
		owned.session.Close()
	}
	if owned.engine != nil {
		owned.engine.Close()
	}
	if owned.endpoint != nil {
		owned.endpoint.Close()
		owned.endpoint.Wait()
	}
	if owned.fd >= 0 {
		unix.Close(owned.fd)
	}
	owned.network.Close()
	C.fcRestrictedRelease(owned.owner)
	current = nil
	return 1
}

//export fcRestrictedReadiness
func fcRestrictedReadiness(directory string) *C.char {
	result := wholedevice.InspectReadiness(filepath.Join(directory, "family.json"), filepath.Join(directory, "bootstrap.json"), time.Now())
	raw, _ := json.Marshal(result)
	return C.CString(string(raw))
}

func main() {}
