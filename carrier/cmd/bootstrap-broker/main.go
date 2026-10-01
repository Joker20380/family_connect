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
	duration := flag.Duration("duration", 10*time.Minute, "isolated process/seed lifetime, at most one hour")
	export := flag.String("directory-export", "", "optional protected READY seed snapshot for Friends control")
	flag.Parse()
	host, _, err := net.SplitHostPort(*address)
	if err != nil || net.ParseIP(host) == nil || *duration <= 0 || *duration > bootstrap.MaxAge {
		return roombroker.Code("invalid_options")
	}
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		return err
	}
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
	config, err := roombroker.ServerTLS(*path)
	if err != nil {
		return err
	}
	var output sync.Mutex
	emit := func(event string) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "utc": time.Now().UTC()})
	}
	broker, err := roombroker.New(provider, roombroker.TelemostGateway{CredentialsPath: *path, Event: emit}, roombroker.DefaultLimits(), func(state roombroker.State, _ roombroker.Code) { emit(string(state)) })
	if err != nil {
		return err
	}
	defer broker.Close()
	listener, err := net.Listen("tcp", *address)
	if err != nil {
		return roombroker.Code("listen_failed")
	}
	defer listener.Close()
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithTimeout(ctx, *duration)
	defer cancel()
	manager := &bootstrap.SeedManager{Event: emit}
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
			return cache.Store(raw, time.Now())
		}
	}
	server := &http.Server{Handler: manager.Handler(*path), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: 5 * time.Second, IdleTimeout: time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	defer server.Close()
	seedDone, httpDone := make(chan error, 1), make(chan error, 1)
	go func() {
		seedDone <- manager.Run(ctx, provider, bootstrap.TelemostSeed, credentials.Family, credentials.Gateway, *duration, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			bootstrap.OpenServer(ctx, endpoint, *path, broker, emit)
		})
	}()
	go func() { httpDone <- server.Serve(tls.NewListener(netutil.LimitListener(listener, 8), config)) }()
	select {
	case <-ctx.Done():
		cancel()
		server.Close()
		<-seedDone
		<-httpDone
		return nil
	case err := <-seedDone:
		cancel()
		server.Close()
		<-httpDone
		return err
	case err := <-httpDone:
		cancel()
		<-seedDone
		return err
	}
}
