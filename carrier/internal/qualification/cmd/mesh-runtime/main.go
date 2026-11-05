package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"net/netip"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/gatewayruntime"
	"github.com/Joker20380/family_connect/carrier/internal/qualification"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "isolated runtime stopped:", err)
		os.Exit(1)
	}
}

func run() error {
	mode := flag.String("mode", "", "relay, gateway, client or admission-probe; never a production provider")
	address := flag.String("listen", "127.0.0.1:0", "local listen address")
	relay := flag.String("relay", "", "isolated packet relay")
	profile := flag.String("family-config", "", "synthetic private profile")
	directory := flag.String("directory-export", "", "SeedManager publication")
	observer := flag.String("publication-observer", "", "same-process reader")
	duration := flag.Duration("duration", time.Hour, "bounded runtime lifetime")
	echo := flag.String("echo", "", "isolated echo origin")
	https := flag.String("https", "", "isolated HTTPS origin")
	config := flag.String("client-config", "", "private client configuration")
	flag.Parse()
	if os.Getenv("FC_LOCAL_CORE") != "1" {
		return fmt.Errorf("explicit isolated runtime required")
	}
	host, _, err := net.SplitHostPort(*address)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		return fmt.Errorf("loopback listener required")
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	provider := qualification.Provider{Address: *relay}
	var output sync.Mutex
	emit := func(event string) {
		output.Lock()
		defer output.Unlock()
		json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "pid": os.Getpid(), "utc": time.Now().UTC()})
	}
	switch *mode {
	case "relay":
		listener, err := net.Listen("tcp", *address)
		if err != nil {
			return err
		}
		defer listener.Close()
		json.NewEncoder(os.Stdout).Encode(map[string]string{"address": listener.Addr().String()})
		err = qualification.Relay(ctx, listener)
		if ctx.Err() != nil {
			return nil
		}
		return err
	case "gateway":
		if *duration <= 0 || *duration > 8*time.Hour {
			return fmt.Errorf("qualification duration out of bounds")
		}
		seedLifetime, rotateAfter := min(*duration, bootstrap.MaxAge), time.Duration(0)
		if *duration > seedLifetime {
			rotateAfter = seedLifetime * 3 / 4
		}
		echoOrigin, err := netip.ParseAddrPort(*echo)
		if err != nil {
			return err
		}
		httpsOrigin, err := netip.ParseAddrPort(*https)
		if err != nil {
			return err
		}
		starter := roombroker.PacketGateway{TelemostGateway: roombroker.TelemostGateway{CredentialsPath: *profile, Event: emit,
			Services: map[string]netip.AddrPort{"chat-mailbox.family-connect.invalid": echoOrigin, "chat-api.family-connect.invalid": httpsOrigin}}, Connect: provider.Gateway}
		failure := func(failure bootstrap.ExchangeFailure) { emit(failure.Stage + ":" + failure.Reason) }
		state := func(state roombroker.State, reason roombroker.Code) { emit(string(state) + ":" + string(reason)) }
		return gatewayruntime.Run(ctx, gatewayruntime.Config{Profile: *profile, Listen: *address, Duration: *duration, SeedLifetime: seedLifetime, RotateAfter: rotateAfter,
			Directory: *directory, Observer: *observer, Event: emit, State: state, AdmissionFailure: failure, ExchangeFailure: failure}, provider, provider.Seed, starter)
	case "client":
		return qualification.Client(ctx, provider, *config)
	case "admission-probe":
		return qualification.AdmissionProbe(ctx, provider, *profile, *directory)
	default:
		return fmt.Errorf("unsupported qualification mode")
	}
}
