//go:build (linux || android) && cgo

package main

/*
#cgo LDFLAGS: -Wl,--wrap=getaddrinfo
void fc_deny_dns(void);
void fc_reset_dns_count(void);
unsigned long fc_dns_count(void);
*/
import "C"

func dnsGuardSupported() bool { return true }
func dnsGuardBlock()          { C.fc_deny_dns() }
func dnsGuardResetCount()     { C.fc_reset_dns_count() }
func dnsGuardCount() uint64   { return uint64(C.fc_dns_count()) }
