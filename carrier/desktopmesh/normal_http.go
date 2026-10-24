package desktopmesh

import (
	"bytes"
	"context"
	"io"
	"net/http"

	"github.com/Joker20380/family_connect/carrier/underlay"
)

type NormalHTTPS struct {
	client *http.Client
	origin string
}

func NewNormalHTTPS(network *underlay.Network) (*NormalHTTPS, error) {
	if network == nil {
		return nil, ErrConfiguration
	}
	client := network.HTTPClient()
	client.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
	return &NormalHTTPS{client: client, origin: readinessOrigin}, nil
}

func (transport *NormalHTTPS) Close() { transport.client.CloseIdleConnections() }

func (transport *NormalHTTPS) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	if (path != "/friends/challenge" && path != "/friends/configuration/ru" && path != "/friends/configuration/nl") ||
		!validProbeID(probe) || len(body) == 0 || len(body) > 8192 {
		return nil, ErrConfiguration
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, transport.origin+path, bytes.NewReader(body))
	if err != nil {
		return nil, ErrConfiguration
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Accept-Encoding", "identity")
	request.Header.Set("X-FC-Probe-ID", probe)
	response, err := transport.client.Do(request)
	if err != nil {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return nil, readinessNetworkFailure(path, err)
	}
	defer response.Body.Close()
	if response.StatusCode == 401 || response.StatusCode == 403 || response.StatusCode == 409 {
		return nil, &ReadinessFailure{Code: "AUTHORIZATION_REJECTED", Authorization: true}
	}
	if response.StatusCode != 200 {
		temporary := response.StatusCode == 429 || response.StatusCode >= 500 && response.StatusCode <= 599
		return nil, &ReadinessFailure{Code: "NORMAL_FETCH_REJECTED", Availability: temporary}
	}
	if encoding := response.Header.Get("Content-Encoding"); encoding != "" && encoding != "identity" {
		return nil, ErrConfiguration
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, MaxNormalResponse+1))
	if ctx.Err() != nil {
		clear(raw)
		return nil, ctx.Err()
	}
	if err != nil || len(raw) == 0 || len(raw) > MaxNormalResponse {
		clear(raw)
		return nil, ErrConfiguration
	}
	return raw, nil
}
