package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"golang.org/x/net/netutil"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func main() {
	observer := newFatalObserver()
	defer receiptPanic(observer)
	err := runObserved(observer)
	observedSignal := ""
	select {
	case received := <-observer.signals:
		if received == syscall.SIGTERM {
			observedSignal = "SIGTERM"
		} else {
			observedSignal = "SIGINT"
		}
	default:
	}
	observer.finish(err, observedSignal, false)
	if err != nil {
		fmt.Fprintln(os.Stderr, "bootstrap broker stopped")
		os.Exit(1)
	}
}

func receiptPanic(observer *fatalObserver) {
	if recover() != nil {
		observer.finish(nil, "", true)
		os.Exit(2)
	}
}

func runObserved(observer *fatalObserver) (result error) {
	defer func() {
		if result != nil {
			observer.failure(bootstrap.SeedFailure{Stage: observer.valueStage(), Cause: result})
		}
		observer.cleanup()
	}()
	path := flag.String("family-config", "", "private gateway profile")
	address := flag.String("listen", "127.0.0.1:18444", "isolated mTLS cache preparation endpoint")
	duration := flag.Duration("duration", 10*time.Minute, "isolated process/seed lifetime, at most four hours; long windows require compatible clients")
	rotateAfter := flag.Duration("seed-rotate-after", 0, "optional single READY seed replacement; retain previous seed until its original deadline")
	export := flag.String("directory-export", "", "optional protected READY seed snapshot for Friends control")
	chatServices := flag.Bool("chat-services", false, "enable pinned Friends API and mailbox services alongside public VPN destinations")
	peerEvidence := flag.String("research-peer-evidence", "", "protected temporary metadata directory; disabled after twenty minutes")
	ownershipEvidence := flag.String("research-admission-evidence", "", "exclusive protected ownership file; at most 512 events and fifteen minutes")
	flag.Parse()
	peerSink, startupSink, stopPeer, err := newPeerEvidence(*peerEvidence)
	if err != nil {
		return err
	}
	defer stopPeer()
	host, _, err := net.SplitHostPort(*address)
	if err != nil || net.ParseIP(host) == nil || *duration <= 0 || *duration > bootstrap.MaxAge || *rotateAfter < 0 || *rotateAfter > 0 && *duration-*rotateAfter <= roombroker.CreationTimeout+bootstrap.ConnectTimeout {
		return roombroker.Code("invalid_options")
	}
	observer.stage("SEED_CREATE")
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		return err
	}
	observer.stage("PROFILE")
	raw, err := roombroker.LoadCredentials(*path)
	if err != nil {
		return err
	}
	var credentials familysession.Credentials
	err = json.Unmarshal(raw, &credentials)
	clear(raw)
	if err != nil {
		return roombroker.Code("credentials_rejected")
	}
	observer.credentials(credentials)
	config, err := roombroker.ServerTLS(*path)
	if err != nil {
		return err
	}
	var output sync.Mutex
	journalSink, stopTrace := bufferedTrace(func(event sessiontrace.Event) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "restricted_trace", "trace": event})
	})
	defer stopTrace()
	traceSink := func(event sessiontrace.Event) bool {
		peerSink(event)
		return journalSink(event)
	}
	emit := func(event string) {
		startupSink(event, "", "")
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "utc": time.Now().UTC()})
	}
	diagnostic := func(report sessiondiag.Report) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "session_terminal", "utc": time.Now().UTC(), "diagnostic": report})
	}
	observer.stage("BROKER")
	broker, err := roombroker.New(provider, roombroker.TelemostGateway{CredentialsPath: *path, Event: emit, Diagnostic: diagnostic, Services: pinnedChatServices(*chatServices), AllowInternet: true}, roombroker.DefaultLimits(), func(state roombroker.State, code roombroker.Code) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": string(state), "utc": time.Now().UTC(), "reason": brokerReason(code)})
	}, traceSink)
	if err != nil {
		return err
	}
	observer.stage("BROKER")
	stopOwnership, err := startOwnershipEvidence(broker, *ownershipEvidence)
	if err != nil {
		emit("admission_observation_unavailable")
		stopOwnership = func() {}
	}
	defer stopOwnership()
	defer broker.Close()
	observer.stage("LISTENER")
	listener, err := net.Listen("tcp", *address)
	if err != nil {
		return roombroker.Code("listen_failed")
	}
	defer listener.Close()
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	observer.signals = make(chan os.Signal, 1)
	signal.Notify(observer.signals, os.Interrupt, syscall.SIGTERM)
	defer signal.Stop(observer.signals)
	ctx, cancel := context.WithTimeout(ctx, *duration)
	defer cancel()
	manager := &bootstrap.SeedManager{Event: emit, RotateAfter: *rotateAfter, Observe: observer.failure}
	if *export != "" {
		if !filepath.IsAbs(*export) {
			return roombroker.Code("invalid_options")
		}
		cache := &bootstrap.Cache{Path: *export, Family: credentials.Family, Gateway: credentials.Gateway}
		manager.Publish = func(directory bootstrap.Directory) error {
			raw, err := json.Marshal(directory)
			if err != nil {
				return err
			}
			err = cache.Store(raw, time.Now())
			if err == nil {
				observer.directory(raw)
			}
			return err
		}
	}
	server := &http.Server{Handler: manager.Handler(*path), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: 5 * time.Second, IdleTimeout: time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	defer server.Close()
	seedDone, httpDone := make(chan error, 1), make(chan error, 1)
	observer.stage("SEED_RUN")
	go func() {
		defer receiptPanic(observer)
		seedDone <- manager.Run(ctx, provider, bootstrap.TelemostSeed, credentials.Family, credentials.Gateway, *duration, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			bootstrap.OpenServer(ctx, endpoint, *path, broker, emit, func(failure bootstrap.ExchangeFailure) {
				startupSink("bootstrap_exchange_rejected", failure.Stage, failure.Reason)
				output.Lock()
				defer output.Unlock()
				_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": "bootstrap_exchange_rejected", "utc": time.Now().UTC(), "stage": failure.Stage, "reason": failure.Reason})
			})
		})
	}()
	go func() {
		defer receiptPanic(observer)
		httpDone <- server.Serve(tls.NewListener(netutil.LimitListener(listener, 8), config))
	}()
	select {
	case <-ctx.Done():
		observer.failure(bootstrap.SeedFailure{Stage: "RUN", Cause: ctx.Err(), ParentError: ctx.Err()})
		observer.cleanup()
		cancel()
		server.Close()
		<-seedDone
		<-httpDone
		return nil
	case err := <-seedDone:
		if err != nil {
			observer.failure(bootstrap.SeedFailure{Stage: "SEED_RUN", Cause: err, ParentError: ctx.Err()})
		}
		observer.cleanup()
		cancel()
		server.Close()
		<-httpDone
		return err
	case err := <-httpDone:
		if err != nil {
			observer.failure(bootstrap.SeedFailure{Stage: "HTTP_SERVE", Cause: err, ParentError: ctx.Err()})
		}
		observer.cleanup()
		cancel()
		<-seedDone
		return err
	}
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
