package main

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"regexp"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
)

const authorityURL = "https://185.251.89.19:8443"

func entryBackend(address string) (coldprovision.Backend, error) {
	if address != authorityURL {
		return coldprovision.LoopbackBackend(address)
	}
	return authorityBackend(&http.Transport{Proxy: nil, DisableKeepAlives: true, MaxResponseHeaderBytes: 4096}), nil
}

func authorityBackend(transport http.RoundTripper) coldprovision.Backend {
	client := &http.Client{Transport: transport, Timeout: 10 * time.Second,
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	requestID := regexp.MustCompile(`^[0-9a-f]{32}$`)
	return func(ctx context.Context, request coldprovision.Request) (coldprovision.Reply, error) {
		if request.Path != coldprovision.Challenge && request.Path != coldprovision.Fetch ||
			!requestID.MatchString(request.ID) || len(request.Body) > coldprovision.MaxMessage {
			return coldprovision.Reply{}, coldprovision.ErrRejected
		}
		message, err := http.NewRequestWithContext(ctx, "POST", authorityURL+request.Path, bytes.NewReader(request.Body))
		if err != nil {
			return coldprovision.Reply{}, err
		}
		message.Header.Set("Content-Type", "application/json")
		message.Header.Set("X-FC-Probe-ID", request.ID)
		response, err := client.Do(message)
		if err != nil {
			return coldprovision.Reply{}, err
		}
		defer response.Body.Close()
		raw, err := io.ReadAll(io.LimitReader(response.Body, coldprovision.MaxMessage+1))
		if err != nil || len(raw) > coldprovision.MaxMessage {
			return coldprovision.Reply{}, coldprovision.ErrRejected
		}
		return coldprovision.Reply{Status: response.StatusCode, Body: raw}, nil
	}
}
