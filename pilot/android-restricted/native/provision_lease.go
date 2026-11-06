package main

import (
	"context"
	"sync"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
)

type provisioningClient interface {
	Post(string, []byte, string) (coldprovision.Reply, error)
	Close()
}

type provisioningLease struct {
	ctx        context.Context
	cancel     context.CancelFunc
	ready      chan struct{}
	client     provisioningClient
	err        error
	diagnostic *coldprovision.Diagnostic
}

var provisioningMu sync.Mutex
var provisioningSequence int64
var provisioningLeases = map[int64]*provisioningLease{}

func reserveProvisioning(lease *provisioningLease) int64 {
	provisioningMu.Lock()
	defer provisioningMu.Unlock()
	if len(provisioningLeases) >= 2 {
		return 0
	}
	provisioningSequence++
	handle := provisioningSequence
	lease.diagnostic.Handle(handle)
	provisioningLeases[handle] = lease
	return handle
}

func findProvisioning(handle int64, remove bool) *provisioningLease {
	provisioningMu.Lock()
	defer provisioningMu.Unlock()
	lease := provisioningLeases[handle]
	if remove {
		delete(provisioningLeases, handle)
	}
	return lease
}

func (lease *provisioningLease) open(open func() (provisioningClient, error)) {
	lease.client, lease.err = open()
	lease.diagnostic.Failure(lease.err)
	close(lease.ready)
	if lease.err != nil || lease.client == nil {
		lease.cancel()
		return
	}
	defer lease.client.Close()
	<-lease.ctx.Done()
}

func (lease *provisioningLease) post(path string, body []byte, requestID string) (coldprovision.Reply, error) {
	<-lease.ready
	if lease.err != nil {
		return coldprovision.Reply{}, lease.err
	}
	if err := lease.ctx.Err(); err != nil {
		lease.diagnostic.Failure(err)
		return coldprovision.Reply{}, err
	}
	if lease.client == nil {
		return coldprovision.Reply{}, coldprovision.ErrUnavailable
	}
	return lease.client.Post(path, body, requestID)
}

func (lease *provisioningLease) close() {
	lease.diagnostic.Close(false)
	lease.cancel()
}
