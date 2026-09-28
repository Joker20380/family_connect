//go:build !cgo || (!linux && !android)

package main

func dnsGuardSupported() bool { return false }
func dnsGuardBlock()          {}
func dnsGuardResetCount()     {}
func dnsGuardCount() uint64   { return 0 }
