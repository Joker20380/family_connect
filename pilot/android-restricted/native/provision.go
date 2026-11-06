//go:build android

package main

// #include <stdint.h>
// #include <stdlib.h>
// int fcRestrictedProtect(uintptr_t owner, int fd);
// void fcRestrictedRelease(uintptr_t owner);
import "C"

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

type provisioningLease struct {
	ctx    context.Context
	cancel context.CancelFunc
	ready  chan struct{}
	client *coldprovision.Client
	err    error
}

var provisioningMu sync.Mutex
var provisioningSequence int64
var provisioningLeases = map[int64]*provisioningLease{}

//export fcProvisionBegin
func fcProvisionBegin(locator, anchor, gateway, resolver string, budget int64, owner C.uintptr_t) int64 {
	locator, anchor, gateway, resolver = strings.Clone(locator), strings.Clone(anchor), strings.Clone(gateway), strings.Clone(resolver)
	if budget <= 0 || budget > 30000 {
		C.fcRestrictedRelease(owner)
		return 0
	}
	if _, _, err := coldprovision.Verify([]byte(locator), []byte(anchor), gateway, time.Now()); err != nil {
		C.fcRestrictedRelease(owner)
		return 0
	}
	provisioningMu.Lock()
	defer provisioningMu.Unlock()
	if len(provisioningLeases) >= 2 {
		C.fcRestrictedRelease(owner)
		return 0
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(budget)*time.Millisecond)
	lease := &provisioningLease{ctx: ctx, cancel: cancel, ready: make(chan struct{})}
	provisioningSequence++
	handle := provisioningSequence
	provisioningLeases[handle] = lease
	go func() {
		defer C.fcRestrictedRelease(owner)
		network, err := underlay.New(ctx, resolver, func(fd int) bool { return C.fcRestrictedProtect(owner, C.int(fd)) != 0 })
		if err != nil {
			lease.err = err
			close(lease.ready)
			cancel()
			return
		}
		defer network.Close()
		lease.client, lease.err = coldprovision.Open(ctx, []byte(locator), []byte(anchor), gateway, coldprovision.Telemost(network))
		close(lease.ready)
		if lease.client == nil {
			cancel()
			return
		}
		defer lease.client.Close()
		<-ctx.Done()
	}()
	return handle
}

//export fcProvisionPost
func fcProvisionPost(handle int64, path, body, requestID string) *C.char {
	provisioningMu.Lock()
	lease := provisioningLeases[handle]
	provisioningMu.Unlock()
	if lease == nil {
		return nil
	}
	select {
	case <-lease.ctx.Done():
		return nil
	case <-lease.ready:
	}
	if lease.err != nil {
		if errors.Is(lease.err, coldprovision.ErrRejected) {
			return C.CString(`{"status":0,"body":{}}`)
		}
		return nil
	}
	reply, err := lease.client.Post(path, []byte(body), requestID)
	if err != nil || lease.ctx.Err() != nil {
		return nil
	}
	raw, err := json.Marshal(reply)
	if err != nil {
		return nil
	}
	return C.CString(string(raw))
}

//export fcProvisionClose
func fcProvisionClose(handle int64) {
	provisioningMu.Lock()
	lease := provisioningLeases[handle]
	delete(provisioningLeases, handle)
	provisioningMu.Unlock()
	if lease != nil {
		lease.cancel()
	}
}
