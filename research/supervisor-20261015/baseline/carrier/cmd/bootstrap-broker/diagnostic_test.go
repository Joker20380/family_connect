package main

import (
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"testing"
)

func TestBrokerReasonIsAnEnum(test *testing.T) {
	for _, code := range []roombroker.Code{"authorization_changed", "lifetime_expired", "gateway_session_failed", "provider_timeout", "provider_forbidden"} {
		if brokerReason(code) != string(code) {
			test.Fatal("reason lost")
		}
	}
	if brokerReason(roombroker.Code("https://private/?token=secret")) != "unknown" {
		test.Fatal("raw error exposed")
	}
}
