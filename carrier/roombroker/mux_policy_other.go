//go:build !linux

package roombroker

func muxCreditPolicy() (bool, error) { return false, nil }
func muxCountersEnabled() bool       { return false }
