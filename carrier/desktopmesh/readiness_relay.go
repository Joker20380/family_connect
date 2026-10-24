package desktopmesh

import (
	"context"
	"encoding/base64"
	"encoding/json"
)

const MaxReadinessRelay = 90000

type ReadinessRelayRequest func(context.Context, string, []byte) ([]byte, error)

type ReadinessRelay struct{ request ReadinessRelayRequest }

func NewReadinessRelay(request ReadinessRelayRequest) (*ReadinessRelay, error) {
	if request == nil {
		return nil, ErrConfiguration
	}
	return &ReadinessRelay{request: request}, nil
}

func (relay *ReadinessRelay) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	if !readinessPath(path) || !validProbeID(probe) || len(body) == 0 || len(body) > 8192 {
		return nil, ErrConfiguration
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	raw, err := relay.request(ctx, path, body)
	defer clear(raw)
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if err != nil {
		return nil, err
	}
	var fields map[string]json.RawMessage
	if strictReadinessJSON(raw, MaxReadinessRelay, &fields) != nil || len(fields) != 2 || fields["status"] == nil || fields["body"] == nil {
		return nil, &ReadinessFailure{Code: "RELAY_INCOMPATIBLE_RESPONSE"}
	}
	var envelope struct {
		Status int    `json:"status"`
		Body   string `json:"body"`
	}
	if strictReadinessJSON(raw, MaxReadinessRelay, &envelope) != nil || envelope.Status < 100 || envelope.Status > 599 {
		return nil, &ReadinessFailure{Code: "RELAY_INCOMPATIBLE_RESPONSE"}
	}
	if err := readinessStatus(path, envelope.Status); err != nil {
		return nil, err
	}
	decoded, err := base64.StdEncoding.DecodeString(envelope.Body)
	if err != nil || len(decoded) == 0 || len(decoded) > 65536 || base64.StdEncoding.EncodeToString(decoded) != envelope.Body {
		clear(decoded)
		return nil, &ReadinessFailure{Code: "RELAY_INCOMPATIBLE_RESPONSE"}
	}
	return decoded, nil
}
