//go:build fc_owner_diagnostic

package startupdiag

import (
	"context"
	"crypto/x509"
	"errors"
	"io"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type key struct{}
type recorder struct {
	mu      sync.Mutex
	started time.Time
	result  Result
}

func Start(ctx context.Context, attempt int64) context.Context {
	started := time.Now()
	return context.WithValue(ctx, key{}, &recorder{started: started, result: Result{
		Schema: 1, Attempt: attempt, StartedUnixMS: started.UnixMilli(), CompletedMS: -1,
		ObservedMS: -1, Status: "RUNNING", Stage: "STARTUP", Cause: "NONE",
	}})
}

func get(ctx context.Context) *recorder {
	record, _ := ctx.Value(key{}).(*recorder)
	return record
}

func stageCode(stage string) string {
	switch stage {
	case "STARTUP", "PROFILE", "DIRECTORY", "SEED_CREATE", "SEED_CONNECT", "SEED_ADMISSION", "SEED_READ",
		"FAMILY_AUTH", "HELLO_RECEIVE", "REQUEST_SEND", "DESCRIPTOR_RECEIVE", "DESCRIPTOR_VALIDATE", "BYE_SEND", "BYE_RECEIVE",
		"DEDICATED_CREATE", "DEDICATED_CONNECT", "DEDICATED_AUTH", "DEDICATED_BIND", "DEDICATED_MUX", "CONTROL_REFRESH":
		return stage
	}
	return "UNKNOWN"
}

func causeCode(err error) string {
	if errors.Is(err, context.Canceled) {
		return "CANCELLED"
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return "DEADLINE"
	}
	var invalid x509.CertificateInvalidError
	if errors.As(err, &invalid) {
		if invalid.Reason == x509.Expired {
			return "CERTIFICATE_TIME_INVALID"
		}
		return "CERTIFICATE_INVALID"
	}
	var authority x509.UnknownAuthorityError
	if errors.As(err, &authority) {
		return "CERTIFICATE_AUTHORITY"
	}
	var hostname x509.HostnameError
	if errors.As(err, &hostname) {
		return "CERTIFICATE_HOSTNAME"
	}
	if errors.Is(err, telemost.ErrAPI) {
		return "PROVIDER_API"
	}
	if errors.Is(err, telemost.ErrClosed) {
		return "CARRIER_CLOSED"
	}
	if errors.Is(err, io.EOF) || errors.Is(err, io.ErrUnexpectedEOF) {
		return "EOF"
	}
	var code roombroker.Code
	if errors.As(err, &code) {
		switch code {
		case "bootstrap_protocol_rejected":
			return "PROTOCOL_REJECTED"
		case "credentials_rejected":
			return "CREDENTIALS_REJECTED"
		case "descriptor_rejected", "dedicated_room_required":
			return "DESCRIPTOR_REJECTED"
		case "descriptor_expired":
			return "DESCRIPTOR_EXPIRED"
		case "exchange_closed":
			return "EXCHANGE_CLOSED"
		}
	}
	return "UNKNOWN"
}

func (record *recorder) failure(stage string, err error) {
	if err == nil || record.result.Complete || record.result.Status != "RUNNING" {
		return
	}
	record.result.Stage, record.result.Cause = stageCode(stage), causeCode(err)
	record.result.Status = "FAILED"
	if record.result.Cause == "CANCELLED" {
		record.result.Status = "CANCELLED"
	}
	record.result.ObservedMS = time.Since(record.started).Milliseconds()
}

func Failure(ctx context.Context, stage string, err error) {
	if record := get(ctx); record != nil {
		record.mu.Lock()
		defer record.mu.Unlock()
		record.failure(stage, err)
	}
}

func Cancel(ctx context.Context) { Failure(ctx, "STARTUP", context.Canceled) }

func Complete(ctx context.Context, err error) {
	if record := get(ctx); record != nil {
		record.mu.Lock()
		defer record.mu.Unlock()
		if record.result.Complete {
			return
		}
		record.failure("STARTUP", err)
		if record.result.Status == "RUNNING" {
			record.result.Status = "SUCCEEDED"
		}
		record.result.Complete = true
		record.result.CompletedMS = time.Since(record.started).Milliseconds()
	}
}

func Snapshot(ctx context.Context) *Result {
	if record := get(ctx); record != nil {
		record.mu.Lock()
		defer record.mu.Unlock()
		result := record.result
		return &result
	}
	return nil
}
