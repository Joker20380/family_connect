package desktopmesh

import (
	"bytes"
	"context"
	"errors"
	"testing"
	"time"
)

func causeCache(test *testing.T, state string) (*ReadinessCache, *ReadinessClient, []byte, *time.Time) {
	test.Helper()
	raw, public, anchor, now := signedReadiness(test, false)
	cache, err := NewReadinessCache(&memoryReadiness{}, public, anchor)
	if err != nil {
		test.Fatal(err)
	}
	if state != "missing" {
		if err := cache.Accept(raw, cacheAttempt(), now); err != nil {
			test.Fatal(err)
		}
	}
	if state == "expired" {
		now = now.Add(21 * time.Minute)
	}
	client := testReadinessClient(test)
	client.clock = func() time.Time { return now }
	return cache, client, raw, &now
}

func TestReadinessPreservesFetchCauseWithUnusableCache(test *testing.T) {
	for _, state := range []string{"expired", "missing"} {
		for _, code := range []string{"CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE", "FETCH_NETWORK_FAILURE", "FETCH_TEMPORARY_SERVER_FAILURE", "RNS_UNAVAILABLE", "RNS_WORKER_UNAVAILABLE"} {
			test.Run(state+"/"+code, func(test *testing.T) {
				cache, client, _, now := causeCache(test, state)
				failure := &ReadinessFailure{Code: code, Availability: true, Network: true}
				calls := 0
				transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
					calls++
					return nil, failure
				})
				raw, source, result, err := ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), false)
				if err != failure || result != "FETCH_FAILED" || raw != nil || source != "" || calls != 1 {
					test.Fatalf("cause lost: error=%v import=%s calls=%d", err, result, calls)
				}
				stored, err := cache.state()
				if err != nil || stored.NextAttempt != now.Unix()+300 {
					test.Fatal("cooldown not persisted")
				}
				_, _, result, err = ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), false)
				expected := ReadinessMissing
				if state == "expired" {
					expected = ReadinessExpired
				}
				if !errors.Is(err, expected) || result != "" || calls != 1 {
					test.Fatal("cooldown performed another fetch or lost cache failure")
				}
				*now = now.Add(300 * time.Second)
				_, _, result, err = ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), false)
				if err != failure || result != "FETCH_FAILED" || calls != 2 {
					test.Fatal("later boundary did not permit ordinary fetch")
				}
			})
		}
	}
}

func TestReadinessRelayCauseSurvivesExpiredCache(test *testing.T) {
	cache, client, _, _ := causeCache(test, "expired")
	directCalls, relayCalls := 0, 0
	failure := &ReadinessFailure{Code: "RNS_UNAVAILABLE", Availability: true, Network: true}
	route, err := NewReadinessRoute(readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
		directCalls++
		return nil, &ReadinessFailure{Code: "CHALLENGE_TIMEOUT", Availability: true, Network: true}
	}), readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
		relayCalls++
		return nil, failure
	}))
	if err != nil {
		test.Fatal(err)
	}
	_, _, result, err := ResolveReadinessWithResult(context.Background(), cache, client, route, cacheAttempt(), true)
	if err != failure || result != "FETCH_FAILED" || directCalls != 1 || relayCalls != 1 {
		test.Fatalf("relay cause lost: %v import=%s direct=%d relay=%d", err, result, directCalls, relayCalls)
	}
}

func TestReadinessValidCacheFallbackAndFailClosedCauses(test *testing.T) {
	for _, code := range []string{"CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE", "TLS_TRUST_REJECTED", "FETCH_INCOMPATIBLE_RESPONSE", "RNS_PROTOCOL_REJECTED", "CHALLENGE_UNAUTHORIZED", "MALFORMED"} {
		test.Run(code, func(test *testing.T) {
			cache, client, cached, now := causeCache(test, "valid")
			failure := &ReadinessFailure{Code: code, Availability: code == "CHALLENGE_TIMEOUT", Network: code == "CHALLENGE_TIMEOUT", Authorization: code == "CHALLENGE_UNAUTHORIZED"}
			transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
				if code == "MALFORMED" {
					return []byte(`{"challenge":`), nil
				}
				if code == "CHALLENGE_TEMPORARY_SERVER_FAILURE" {
					return nil, readinessStatus("/friends/restricted-readiness/challenge", 503)
				}
				return nil, failure
			})
			raw, source, result, err := ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), true)
			switch code {
			case "CHALLENGE_TIMEOUT", "CHALLENGE_TEMPORARY_SERVER_FAILURE":
				if err != nil || source != ReadinessSaved || result != "FETCH_FAILED" || !bytes.Equal(raw, cached) {
					test.Fatal("validated cache fallback changed")
				}
			case "CHALLENGE_UNAUTHORIZED":
				_, status := cache.Usable(*now)
				if !errors.Is(err, ReadinessDenied) || result != ReadinessDenied || status != ReadinessDenied || raw != nil {
					test.Fatal("authorization denial lost durable latch")
				}
			default:
				if err == nil || raw != nil || source != "" || result != "FETCH_FAILED" || (code != "MALFORMED" && err != failure) {
					test.Fatal("trust/protocol failure used cached material")
				}
			}
		})
	}
}

func TestReadinessCancellationAroundFailedFetch(test *testing.T) {
	for _, before := range []bool{true, false} {
		cache, client, _, _ := causeCache(test, "valid")
		ctx, cancel := context.WithCancel(context.Background())
		calls := 0
		if before {
			cancel()
		}
		transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
			calls++
			cancel()
			return nil, &ReadinessFailure{Code: "CHALLENGE_TIMEOUT", Availability: true, Network: true}
		})
		raw, source, _, err := ResolveReadinessWithResult(ctx, cache, client, transport, cacheAttempt(), true)
		cancel()
		if !errors.Is(err, context.Canceled) || raw != nil || source != "" || (before && calls != 0) || (!before && calls != 1) {
			test.Fatal("cancelled resolver fetched or returned cached material")
		}
	}
}
