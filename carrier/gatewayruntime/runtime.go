package gatewayruntime

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"io"
	"log"
	"net"
	"net/http"
	"path/filepath"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"golang.org/x/net/netutil"
)

type Config struct {
	Profile, Listen, Directory, Observer string
	Duration                             time.Duration
	SeedLifetime, RotateAfter            time.Duration
	Event                                func(string)
	State                                func(roombroker.State, roombroker.Code)
	Trace                                func(sessiontrace.Event) bool
	AdmissionFailure, ExchangeFailure    func(bootstrap.ExchangeFailure)
}

func Run(parent context.Context, options Config, provider roombroker.RoomProvider, connect bootstrap.SeedConnector, starter roombroker.GatewayStarter) error {
	if options.Event == nil {
		options.Event = func(string) {}
	}
	if options.SeedLifetime == 0 {
		options.SeedLifetime = options.Duration
	}
	host, _, err := net.SplitHostPort(options.Listen)
	if err != nil || net.ParseIP(host) == nil || options.Duration <= 0 || options.SeedLifetime <= 0 || options.SeedLifetime > bootstrap.MaxAge ||
		provider == nil || connect == nil || starter == nil || options.Directory != "" && !filepath.IsAbs(options.Directory) {
		return roombroker.Code("invalid_options")
	}
	raw, err := roombroker.LoadCredentials(options.Profile)
	if err != nil {
		return err
	}
	var credentials familysession.Credentials
	err = json.Unmarshal(raw, &credentials)
	clear(raw)
	if err != nil {
		return roombroker.Code("credentials_rejected")
	}
	configuration, err := roombroker.ServerTLS(options.Profile)
	if err != nil {
		return err
	}
	broker, err := roombroker.New(provider, starter, roombroker.DefaultLimits(), options.State, options.Trace)
	if err != nil {
		return err
	}
	defer broker.Close()
	listener, err := net.Listen("tcp", options.Listen)
	if err != nil {
		return roombroker.Code("listen_failed")
	}
	defer listener.Close()
	ctx, cancel := context.WithTimeout(parent, options.Duration)
	defer cancel()
	if options.Observer != "" {
		closeObserver, err := roombroker.ObservePublication(ctx, options.Observer, options.Profile)
		if err != nil {
			return err
		}
		defer closeObserver()
	}
	manager := &bootstrap.SeedManager{Event: options.Event, RotateAfter: options.RotateAfter}
	if options.Directory != "" {
		cache := &bootstrap.Cache{Path: options.Directory, Family: credentials.Family, Gateway: credentials.Gateway}
		manager.Publish = func(directory bootstrap.Directory) error {
			raw, err := json.Marshal(directory)
			if err != nil {
				return err
			}
			return cache.Store(raw, time.Now())
		}
	}
	server := &http.Server{Handler: manager.Handler(options.Profile), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 5 * time.Second,
		WriteTimeout: 5 * time.Second, IdleTimeout: time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	defer server.Close()
	seedDone, httpDone := make(chan error, 1), make(chan error, 1)
	go func() {
		seedDone <- manager.Run(ctx, provider, connect, credentials.Family, credentials.Gateway, options.SeedLifetime, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			bootstrap.OpenServerObserved(ctx, endpoint, options.Profile, broker, options.Event, options.AdmissionFailure, options.ExchangeFailure)
		})
	}()
	go func() { httpDone <- server.Serve(tls.NewListener(netutil.LimitListener(listener, 8), configuration)) }()
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
