package bootstrap

import (
	"context"
	"errors"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type ExchangeFailure struct {
	Stage  string `json:"stage"`
	Reason string `json:"reason"`
}

func exchangeReason(err error) string {
	var code roombroker.Code
	if errors.As(err, &code) {
		switch code {
		case "unauthorized", "device_busy", "outstanding_limit", "closed", "entropy_unavailable",
			"bootstrap_protocol_rejected", "descriptor_expired", "authorization_changed", "cancelled",
			"stale_or_unbound_setup", "setup_replayed", "descriptor_replayed", "provider_failure", "provider_response", "provider_cancelled",
			"provider_timeout", "provider_transport", "provider_request", "provider_bad_request",
			"provider_unauthorized", "provider_forbidden", "provider_rate_limited", "provider_unavailable",
			"provider_status", "provider_body", "provider_json", "provider_id", "provider_join_url",
			"gateway_failed", "gateway_ready_timeout":
			return string(code)
		}
	}
	if errors.Is(err, context.Canceled) {
		return "context_cancelled"
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return "context_deadline"
	}
	return "unknown"
}
