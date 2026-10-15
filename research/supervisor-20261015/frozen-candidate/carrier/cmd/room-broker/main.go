package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "room broker stopped")
		os.Exit(1)
	}
}

func run() error {
	path := flag.String("family-config", "", "private gateway Family profile")
	address := flag.String("listen", "127.0.0.1:18443", "loopback control endpoint; expose through authenticated ingress")
	duration := flag.Duration("duration", 10*time.Minute, "bounded isolated process lifetime")
	flag.Parse()
	host, _, err := net.SplitHostPort(*address)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() || *duration <= 0 || *duration > time.Hour {
		return errors.New("invalid options")
	}
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		return err
	}
	config, err := roombroker.ServerTLS(*path)
	if err != nil {
		return err
	}
	var output sync.Mutex
	emit := func(event string, code roombroker.Code) {
		output.Lock()
		defer output.Unlock()
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"event": event, "code": code, "utc": time.Now().UTC()})
	}
	broker, err := roombroker.New(provider, roombroker.TelemostGateway{CredentialsPath: *path, Event: func(event string) { emit(event, "") }},
		roombroker.DefaultLimits(), func(state roombroker.State, code roombroker.Code) { emit(string(state), code) })
	if err != nil {
		return err
	}
	defer broker.Close()
	listener, err := net.Listen("tcp", *address)
	if err != nil {
		return err
	}
	defer listener.Close()
	server := &http.Server{Handler: broker.Handler(*path), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second,
		WriteTimeout: 65 * time.Second, IdleTimeout: 5 * time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithTimeout(ctx, *duration)
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- server.Serve(tls.NewListener(listener, config)) }()
	emit("control_ready", "")
	select {
	case <-ctx.Done():
		server.Close()
		<-done
		return nil
	case err := <-done:
		return err
	}
}
