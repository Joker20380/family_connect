package main

import (
	"context"
	"errors"
	"io"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
)

func TestProvisionOpenFailureSurvivesCancelCloseAndOtherHandle(test *testing.T) {
	for iteration := 0; iteration < 100; iteration++ {
		diagnostic := coldprovision.NewDiagnostic(time.Second)
		diagnostic.Stage("CARRIER_OPEN", false)
		ctx, cancel := context.WithCancel(context.Background())
		lease := &provisioningLease{ctx: ctx, cancel: cancel, ready: make(chan struct{}), diagnostic: diagnostic}
		handle := reserveProvisioning(lease)
		if handle == 0 {
			test.Fatal("handle missing")
		}
		selected := findProvisioning(handle, false)
		var workers sync.WaitGroup
		workers.Add(3)
		go func() { defer workers.Done(); lease.open(func() (provisioningClient, error) { return nil, io.EOF }) }()
		go func() { defer workers.Done(); findProvisioning(handle, true).close() }()
		go func() {
			defer workers.Done()
			_, err := selected.post("", nil, "")
			if !errors.Is(err, io.EOF) {
				test.Error("Open cause overwritten by cancellation")
			}
			for count := 0; count < 10; count++ {
				diagnostic.Snapshot()
			}
		}()
		workers.Wait()
		if diagnostic.Snapshot().Reason != "EOF" || !diagnostic.Snapshot().Closed {
			test.Fatal("snapshot lost Open result")
		}
		if findProvisioning(handle, false) != nil {
			test.Fatal("released handle retained")
		}
	}
}

func TestProvisionCancelledAfterOpenDoesNotClaimTLSFailure(test *testing.T) {
	diagnostic := coldprovision.NewDiagnostic(time.Second)
	diagnostic.Stage("TLS_HANDSHAKE", true)
	ctx, cancel := context.WithCancel(context.Background())
	lease := &provisioningLease{ctx: ctx, cancel: cancel, ready: make(chan struct{}), diagnostic: diagnostic}
	close(lease.ready)
	cancel()
	_, err := lease.post("", nil, "")
	result := diagnostic.Snapshot()
	if !errors.Is(err, context.Canceled) || result.FirstFailure != "REQUEST_VALIDATE" || result.LastSuccess != "TLS_HANDSHAKE" || result.Reason != "CANCELLED" {
		test.Fatal("post-Open cancellation misreported")
	}
}
