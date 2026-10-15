package main

import (
	"strings"
	"testing"
)

func TestMuxNegativeDNSUsesReservedDomain(test *testing.T) {
	if !strings.HasSuffix(muxDNSName(2), ".invalid.") {
		test.Fatal("NXDOMAIN probe must not depend on wildcard policy of an ordinary zone")
	}
	for _, index := range []int{0, 1} {
		if muxDNSName(index) != "example.com." {
			test.Fatal("positive DNS proof target changed")
		}
	}
}
