package main

import (
	"context"
	"errors"
	"net"
	"os"
	"time"
)

func prepareDNSGuard() error {
	if !dnsGuardSupported() {
		return errors.New("DNS guard requires isolated native CGO build")
	}
	return os.Setenv("GODEBUG", os.Getenv("GODEBUG")+",netdns=cgo")
}

func activateDNSGuard(ctx context.Context) error {
	dnsGuardBlock()
	ctx, cancel := context.WithTimeout(ctx, time.Second)
	defer cancel()
	_, err := net.DefaultResolver.LookupHost(ctx, "fc-negative-dns-probe.example.com.")
	if err == nil || dnsGuardCount() == 0 {
		return errors.New("negative client DNS condition not established")
	}
	dnsGuardResetCount()
	return nil
}
