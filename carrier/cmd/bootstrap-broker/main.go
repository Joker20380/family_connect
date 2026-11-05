package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/gatewayruntime"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func main() {
	if run() != nil {
		fmt.Fprintln(os.Stderr, "bootstrap broker stopped")
		os.Exit(1)
	}
}

func run() error {
	path := flag.String("family-config", "", "private gateway profile")
	address := flag.String("listen", "127.0.0.1:18444", "isolated mTLS cache preparation endpoint")
	duration := flag.Duration("duration", 10*time.Minute, "isolated process/seed lifetime, at most four hours; long windows require compatible clients")
	export := flag.String("directory-export", "", "optional protected READY seed snapshot for Friends control")
	publication := flag.String("publication-observer", "", "optional root-private online qualification socket")
	flag.Parse()
	host, _, err := net.SplitHostPort(*address)
	if err != nil || net.ParseIP(host) == nil || *duration <= 0 || *duration > bootstrap.MaxAge ||
		*export != "" && !filepath.IsAbs(*export) {
		return roombroker.Code("invalid_options")
	}
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		return err
	}
	var output sync.Mutex
	traceSink, stopTrace := bufferedTrace(func(event sessiontrace.Event) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "restricted_trace", "trace": event})
	})
	defer stopTrace()
	emit := func(event string) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "utc": time.Now().UTC()})
	}
	diagnostic := func(report sessiondiag.Report) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "session_terminal", "utc": time.Now().UTC(), "diagnostic": report})
	}
	state := func(state roombroker.State, code roombroker.Code) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": string(state), "utc": time.Now().UTC(), "reason": brokerReason(code)})
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	admissionFailure := func(failure bootstrap.ExchangeFailure) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "bootstrap_admission_rejected", "utc": time.Now().UTC(), "stage": failure.Stage, "reason": failure.Reason})
	}
	exchangeFailure := func(failure bootstrap.ExchangeFailure) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "bootstrap_exchange_rejected", "utc": time.Now().UTC(), "stage": failure.Stage, "reason": failure.Reason})
	}
	return gatewayruntime.Run(ctx, gatewayruntime.Config{Profile: *path, Listen: *address, Duration: *duration,
		Directory: *export, Observer: *publication, Event: emit, State: state, Trace: traceSink,
		AdmissionFailure: admissionFailure, ExchangeFailure: exchangeFailure}, provider, bootstrap.TelemostSeed,
		roombroker.TelemostGateway{CredentialsPath: *path, Event: emit, Diagnostic: diagnostic})
}

func brokerReason(code roombroker.Code) string {
	switch code {
	case "", "cancelled", "lifetime_expired", "authorization_changed", "unused_expired", "gateway_session_failed", "gateway_failed", "gateway_ready_timeout",
		"provider_failure", "provider_response", "provider_cancelled", "provider_timeout", "provider_transport", "provider_request", "provider_bad_request", "provider_unauthorized", "provider_forbidden", "provider_rate_limited", "provider_unavailable", "provider_status", "provider_body", "provider_json", "provider_id", "provider_join_url":
		return string(code)
	default:
		return "unknown"
	}
}
