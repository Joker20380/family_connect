//go:build android

package main

// #include <stdint.h>
// #include <stdlib.h>
// int fcProvisionProtect(uintptr_t owner, int fd);
// void fcRestrictedRelease(uintptr_t owner);
import "C"

import (
	"context"
	"encoding/json"
	"strings"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

func provisioningResult(output **C.char, diagnostic *coldprovision.Diagnostic) {
	raw, _ := json.Marshal(diagnostic.Snapshot())
	*output = C.CString(string(raw))
}

//export fcProvisionBegin
func fcProvisionBegin(locator, anchor, gateway, resolver string, budget int64, owner C.uintptr_t, output **C.char) int64 {
	diagnostic := coldprovision.NewDiagnostic(time.Duration(budget) * time.Millisecond)
	defer provisioningResult(output, diagnostic)
	locator, anchor, gateway, resolver = strings.Clone(locator), strings.Clone(anchor), strings.Clone(gateway), strings.Clone(resolver)
	if budget <= 0 || budget > 30000 {
		diagnostic.Failure(coldprovision.ErrRejected)
		C.fcRestrictedRelease(owner)
		diagnostic.Close(true)
		return 0
	}
	diagnostic.Stage("LOCATOR", false)
	if _, _, err := coldprovision.Verify([]byte(locator), []byte(anchor), gateway, time.Now()); err != nil {
		diagnostic.Failure(coldprovision.ErrRejected)
		C.fcRestrictedRelease(owner)
		diagnostic.Close(true)
		return 0
	}
	diagnostic.Stage("LOCATOR", true)
	ctx, cancel := context.WithTimeout(coldprovision.WithDiagnostic(context.Background(), diagnostic), time.Duration(budget)*time.Millisecond)
	lease := &provisioningLease{ctx: ctx, cancel: cancel, ready: make(chan struct{}), diagnostic: diagnostic}
	handle := reserveProvisioning(lease)
	if handle == 0 {
		diagnostic.Failure(coldprovision.ErrUnavailable)
		cancel()
		C.fcRestrictedRelease(owner)
		diagnostic.Close(true)
		return 0
	}
	go func() {
		defer func() { C.fcRestrictedRelease(owner); diagnostic.Close(true) }()
		var network *underlay.Network
		defer func() {
			if network != nil {
				network.Close()
			}
		}()
		lease.open(func() (provisioningClient, error) {
			diagnostic.Stage("UNDERLAY", false)
			var err error
			network, err = underlay.New(ctx, resolver, func(fd int) bool {
				result := int(C.fcProvisionProtect(owner, C.int(fd)))
				diagnostic.ProtectResult(result)
				return result == 1
			})
			if err != nil {
				diagnostic.Failure(err)
				return nil, err
			}
			diagnostic.Stage("UNDERLAY", true)
			client, err := coldprovision.Open(ctx, []byte(locator), []byte(anchor), gateway, coldprovision.Telemost(network))
			if err != nil {
				return nil, err
			}
			return client, nil
		})
	}()
	return handle
}

//export fcProvisionPost
func fcProvisionPost(handle int64, path, body, requestID string, output **C.char) *C.char {
	lease := findProvisioning(handle, false)
	if lease == nil {
		raw, _ := json.Marshal(coldprovision.DiagnosticSnapshot{Handle: handle, GoEntered: true, FirstFailure: "HANDLE", Reason: "CLOSED", Closed: true})
		*output = C.CString(string(raw))
		return nil
	}
	defer provisioningResult(output, lease.diagnostic)
	reply, err := lease.post(path, []byte(body), requestID)
	if err != nil || lease.ctx.Err() != nil {
		if err == nil {
			err = lease.ctx.Err()
		}
		lease.diagnostic.Failure(err)
		return nil
	}
	raw, err := json.Marshal(reply)
	if err != nil {
		lease.diagnostic.Failure(err)
		return nil
	}
	return C.CString(string(raw))
}

//export fcProvisionClose
func fcProvisionClose(handle int64) *C.char {
	lease := findProvisioning(handle, true)
	if lease != nil {
		lease.close()
		var result *C.char
		provisioningResult(&result, lease.diagnostic)
		return result
	}
	return nil
}
