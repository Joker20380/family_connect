package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type matrixProvider struct{ cause error }

func (provider matrixProvider) CreateRoom(context.Context) (roombroker.Room, error) {
	return roombroker.Room{ID: "fixture", JoinURL: "https://telemost.yandex.ru/j/fixture"}, provider.cause
}

type matrixEndpoint struct {
	cause  error
	source string
	onRead func()
	closed atomic.Int32
}

func (endpoint *matrixEndpoint) Recv(context.Context) ([]byte, error) {
	if endpoint.onRead != nil {
		endpoint.onRead()
	}
	return nil, endpoint.cause
}
func (endpoint *matrixEndpoint) SendContext(context.Context, []byte) error { return nil }
func (endpoint *matrixEndpoint) Close() error {
	endpoint.closed.Add(1)
	return errors.New("SECRET cleanup")
}
func (endpoint *matrixEndpoint) SeedCloseSource() string { return endpoint.source }

func TestSeedReadMatrix(test *testing.T) {
	after := os.Getenv("FC_EXPECT_SEED_OBSERVABILITY") == "1"
	for _, item := range []struct {
		name                  string
		cause                 error
		source, before, after string
		cancel                bool
	}{
		{"clean_eof", io.EOF, "", "EOF", "EOF", false},
		{"partial_read", io.ErrUnexpectedEOF, "", "EOF", "EOF", false},
		{"peer_timeout", &net.OpError{Op: "read", Err: os.ErrDeadlineExceeded}, "", "UNKNOWN", "IO_TIMEOUT", false},
		{"caller_deadline", context.DeadlineExceeded, "", "DEADLINE", "DEADLINE", false},
		{"caller_cancel", context.Canceled, "", "CANCELLED", "CANCELLED", true},
		{"remote_reset", fmt.Errorf("SECRET %w", syscall.ECONNRESET), "", "UNKNOWN", "CONNECTION_RESET", false},
		{"local_close", net.ErrClosed, "", "UNKNOWN", "NET_CLOSED", false},
		{"signal_read", errors.New("SECRET signaling read detail"), "SIGNAL_READ", "UNKNOWN", "SIGNAL_READ", false},
		{"queue_full", errors.New("SECRET queue detail"), "RECEIVE_QUEUE_FULL", "UNKNOWN", "RECEIVE_QUEUE_FULL", false},
		{"conference_ended", errors.New("SECRET conference detail"), "CONFERENCE_ENDED", "UNKNOWN", "CONFERENCE_ENDED", false},
		{"unknown", errors.New("SECRET https://private.invalid/token"), "", "UNKNOWN", "UNKNOWN", false},
		{"invalid_source", errors.New("SECRET"), "SECRET|SIGNAL_READ", "UNKNOWN", "UNKNOWN", false},
	} {
		test.Run(item.name, func(test *testing.T) {
			observer := fixtureObserver(test)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			endpoint := &matrixEndpoint{cause: item.cause, source: item.source}
			if item.cancel {
				endpoint.onRead = cancel
			}
			type primaryError struct{ cause error }
			var observed atomic.Pointer[primaryError]
			manager := &bootstrap.SeedManager{RotateAfter: 3 * time.Hour, Observe: func(failure bootstrap.SeedFailure) {
				observed.Store(&primaryError{failure.Cause})
				observer.failure(failure)
			}}
			err := manager.Run(ctx, matrixProvider{}, func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				return endpoint, nil
			}, strings.Repeat("a", 32), strings.Repeat("b", 32), 4*time.Hour, func(context.Context, familysession.PacketEndpoint) { test.Error("unexpected exchange") })
			var primary error
			if value := observed.Load(); value != nil {
				primary = value.cause
			}
			if item.cancel && primary == nil {
				observer.failure(bootstrap.SeedFailure{Stage: "RUN", Cause: err, ParentError: ctx.Err()})
			} else if err != roombroker.Code("seed_closed") || primary != item.cause {
				test.Fatalf("changed legacy return/primary: %T / %T", err, primary)
			}
			observer.failure(bootstrap.SeedFailure{Stage: "RUN", Cause: errors.New("SECRET late cleanup")})
			observer.cleanup()
			observer.finish(err, "", false)
			record := readFatal(test, observer)
			expected := item.before
			if after {
				expected = item.after
			}
			if record.Cause != expected || record.Fatal == item.cancel || endpoint.closed.Load() == 0 {
				test.Fatalf("cause=%s expected=%s fatal=%v closed=%d", record.Cause, expected, record.Fatal, endpoint.closed.Load())
			}
			raw, _ := json.Marshal(record)
			if strings.Contains(string(raw), "SECRET") || strings.Contains(string(raw), "private.invalid") {
				test.Fatal("privacy")
			}
			test.Logf("SEED_MATRIX %s", raw)
		})
	}
}

func TestSeedProviderFailureMatrix(test *testing.T) {
	observer := fixtureObserver(test)
	manager := &bootstrap.SeedManager{Observe: observer.failure}
	err := manager.Run(context.Background(), matrixProvider{roombroker.Code("provider_timeout")},
		func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			test.Fatal("connector must not run")
			return nil, nil
		},
		strings.Repeat("a", 32), strings.Repeat("b", 32), time.Hour, func(context.Context, familysession.PacketEndpoint) {})
	if err != roombroker.Code("seed_creation_failed") {
		test.Fatal("return changed")
	}
	observer.finish(err, "", false)
	record := readFatal(test, observer)
	if record.Stage != "SEED_CREATE" || record.Cause != "provider_timeout" {
		test.Fatal(record)
	}
}
