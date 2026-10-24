package desktopmesh

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"testing"
)

func TestReadinessRelayExactEnvelopeAndStatus(test *testing.T) {
	for _, path := range []string{"/friends/restricted-readiness", "/friends/restricted-readiness/challenge", "/friends/restricted-readiness/ack-challenge", "/friends/restricted-readiness/ack"} {
		for _, status := range []int{200, 401, 403, 429, 500, 302, 409} {
			payload := []byte(`{"test_only":true}`)
			relay, err := NewReadinessRelay(func(ctx context.Context, requested string, body []byte) ([]byte, error) {
				if requested != path || !bytes.Equal(body, payload) {
					test.Fatal("relay rewrote authenticated request")
				}
				return json.Marshal(map[string]any{"status": status, "body": base64.StdEncoding.EncodeToString(payload)})
			})
			if err != nil {
				test.Fatal(err)
			}
			raw, err := relay.Post(context.Background(), path, payload, cacheAttempt().FetchID)
			if status == 200 {
				if err != nil || !bytes.Equal(raw, payload) {
					test.Fatal("valid relay body changed", err)
				}
			} else {
				var failure *ReadinessFailure
				if len(raw) != 0 || !errors.As(err, &failure) || failure.Authorization != (status == 401 || status == 403) ||
					failure.Availability != (status == 429 || status >= 500) || failure.Network {
					test.Fatal("relay authorization/status classification differs", status)
				}
			}
		}
	}
}

func TestReadinessRelayRejectsAmbiguousLargeOrNullEnvelope(test *testing.T) {
	for _, raw := range [][]byte{[]byte(`{}`), []byte(`{"status":200,"body":null}`), []byte(`{"status":200,"body":""}`),
		[]byte(`{"status":200,"status":200,"body":"e30="}`), []byte(`{"status":200,"body":"e30=\n"}`),
		[]byte(`{"status":200,"body":"e30=","extra":true}`), []byte(`{"status":true,"body":"e30="}`),
		bytes.Repeat([]byte("x"), MaxReadinessRelay+1)} {
		relay, _ := NewReadinessRelay(func(context.Context, string, []byte) ([]byte, error) { return bytes.Clone(raw), nil })
		if response, err := relay.Post(context.Background(), "/friends/restricted-readiness", []byte("{}"), cacheAttempt().FetchID); err == nil || len(response) != 0 {
			test.Fatal("invalid relay envelope accepted")
		}
	}
}

func TestReadinessRelayCancellationWinsAndNeverCallsUnknownPath(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	calls := 0
	relay, _ := NewReadinessRelay(func(context.Context, string, []byte) ([]byte, error) {
		calls++
		cancel()
		return []byte(`{"status":200,"body":"e30="}`), nil
	})
	if _, err := relay.Post(ctx, "/exec", []byte("{}"), cacheAttempt().FetchID); err == nil || calls != 0 {
		test.Fatal("unknown path reached RNS")
	}
	if _, err := relay.Post(ctx, "/friends/restricted-readiness", []byte("{}"), cacheAttempt().FetchID); !errors.Is(err, context.Canceled) || calls != 1 {
		test.Fatal("late RNS success overrode cancel")
	}
}
