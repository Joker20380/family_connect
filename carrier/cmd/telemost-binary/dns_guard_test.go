package main

import (
	"context"
	"net"
	"os"
	"os/exec"
	"testing"
)

func TestNativeDNSGuard(test *testing.T) {
	if !dnsGuardSupported() {
		test.Skip("native CGO guard not compiled")
	}
	if os.Getenv("FC_DNS_GUARD_CHILD") == "1" {
		if err := prepareDNSGuard(); err != nil {
			test.Fatal(err)
		}
		if err := activateDNSGuard(context.Background()); err != nil {
			test.Fatal(err)
		}
		if dnsGuardCount() != 0 {
			test.Fatal("probe counter not reset")
		}
		if _, err := net.LookupHost("example.com."); err == nil || dnsGuardCount() == 0 {
			test.Fatal("native DNS escaped guard")
		}
		return
	}
	command := exec.Command(os.Args[0], "-test.run=^TestNativeDNSGuard$")
	command.Env = append(os.Environ(), "FC_DNS_GUARD_CHILD=1", "GODEBUG=netdns=cgo")
	if output, err := command.CombinedOutput(); err != nil {
		test.Fatalf("%v: %s", err, output)
	}
}
