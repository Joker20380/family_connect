package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"net/netip"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func main() {
	directory := flag.String("directory", "", "isolated synthetic test directory")
	flag.Parse()
	var lock sync.Mutex
	emit := func(event, reason string) {
		lock.Lock()
		defer lock.Unlock()
		json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "reason": reason, "unix": time.Now().Unix()})
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithTimeout(ctx, 30*time.Minute)
	defer cancel()
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		emit("PREPARATION_FAILED", "provider_credentials_unavailable")
		return
	}
	path := filepath.Join(*directory, "gateway.json")
	raw, err := roombroker.LoadCredentials(path)
	if err != nil {
		emit("PREPARATION_FAILED", "credentials")
		return
	}
	var credentials familysession.Credentials
	err = json.Unmarshal(raw, &credentials)
	clear(raw)
	if err != nil {
		emit("PREPARATION_FAILED", "credentials")
		return
	}
	services := map[string]netip.AddrPort{
		"chat-api.family-connect.invalid":     netip.MustParseAddrPort("127.0.0.1:38873"),
		"chat-mailbox.family-connect.invalid": netip.MustParseAddrPort("127.0.0.1:38872"),
	}
	broker, err := roombroker.New(provider, roombroker.TelemostGateway{CredentialsPath: path, Services: services, Event: func(event string) { emit(event, "") }}, roombroker.DefaultLimits(), func(state roombroker.State, code roombroker.Code) { emit(string(state), string(code)) }, nil)
	if err != nil {
		emit("PREPARATION_FAILED", "broker")
		return
	}
	defer broker.Close()
	cache := &bootstrap.Cache{Path: filepath.Join(*directory, "seed.json"), Family: credentials.Family, Gateway: credentials.Gateway}
	manager := &bootstrap.SeedManager{Event: func(event string) { emit(event, "") }, Publish: func(value bootstrap.Directory) error {
		raw, err := json.Marshal(value)
		if err != nil {
			return err
		}
		return cache.Store(raw, time.Now())
	}}
	err = manager.Run(ctx, provider, bootstrap.TelemostSeed, credentials.Family, credentials.Gateway, 30*time.Minute, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
		bootstrap.OpenServer(ctx, endpoint, path, broker, func(event string) { emit(event, "") }, func(failure bootstrap.ExchangeFailure) { emit(failure.Stage, failure.Reason) })
	})
	if err != nil {
		reason := "unknown"
		var code roombroker.Code
		if errors.As(err, &code) {
			reason = string(code)
		}
		if errors.Is(err, context.Canceled) {
			reason = "cancelled"
		}
		if errors.Is(err, context.DeadlineExceeded) {
			reason = "deadline"
		}
		emit("SEED_TERMINAL", reason)
	} else {
		emit("CLOSED", "")
	}
}
