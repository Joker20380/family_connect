package startupdiag

import (
	"context"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"errors"
	"io"
	"os"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type key struct{}
type bootstrapKey struct{}
type bootstrapReference struct {
	tag   string
	index int
	owner *recorder
}

func Bootstrap(ctx context.Context, nonce string) context.Context {
	record := get(ctx)
	tag, status := sessiontrace.Tag(nonce)
	if record == nil || status != "VALID" {
		return ctx
	}
	record.mu.Lock()
	defer record.mu.Unlock()
	if record.result.Complete || record.result.Status != "RUNNING" {
		return ctx
	}
	reference := bootstrapReference{tag: tag, index: -1, owner: record}
	if len(record.result.BootstrapExchanges) < BootstrapExchangeLimit {
		reference.index = len(record.result.BootstrapExchanges)
		record.result.BootstrapExchanges = append(record.result.BootstrapExchanges, BootstrapExchange{Tag: tag})
	} else {
		record.result.BootstrapExchangesDropped++
	}
	return context.WithValue(ctx, bootstrapKey{}, reference)
}

func BootstrapAuthenticated(ctx context.Context) {
	reference, ok := ctx.Value(bootstrapKey{}).(bootstrapReference)
	record := get(ctx)
	if !ok || record == nil || reference.owner != record || reference.index < 0 {
		return
	}
	record.mu.Lock()
	defer record.mu.Unlock()
	if !record.result.Complete && record.result.Status == "RUNNING" {
		record.result.BootstrapExchanges[reference.index].FamilyAuthenticated = true
	}
}

type recorder struct {
	mu            sync.Mutex
	started       time.Time
	result        Result
	observedError error
	observation   *Observation
}

func Start(ctx context.Context, attempt int64) context.Context {
	started := time.Now()
	record := &recorder{started: started, result: Result{
		Schema: 1, Attempt: attempt, StartedUnixMS: started.UnixMilli(), CompletedMS: -1,
		ObservedMS: -1, Status: "RUNNING", Stage: "STARTUP", Cause: "NONE",
	}}
	ctx = context.WithValue(ctx, key{}, record)
	return familysession.WatchReceive(ctx, func(observed context.Context, err error) {
		record.mu.Lock()
		defer record.mu.Unlock()
		if record.observation == nil && !record.result.Complete && record.result.Status == "RUNNING" {
			record.observedError = err
			record.observation = record.facts(observed, err, "FAMILY_RECEIVE")
		}
	})
}

func get(ctx context.Context) *recorder {
	record, _ := ctx.Value(key{}).(*recorder)
	return record
}

func stageCode(stage string) string {
	switch stage {
	case "STARTUP", "OWNERSHIP_DRAIN", "PROFILE", "DIRECTORY", "SEED_CREATE", "SEED_CONNECT", "SEED_ADMISSION", "SEED_READ",
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
	if errors.Is(err, os.ErrDeadlineExceeded) {
		return "IO_DEADLINE"
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
	if errors.Is(err, io.ErrClosedPipe) {
		return "CLOSED_PIPE"
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
	var timed interface{ Timeout() bool }
	if errors.As(err, &timed) && timed.Timeout() {
		return "TIMEOUT_UNQUALIFIED"
	}
	return "UNKNOWN"
}

func (record *recorder) facts(ctx context.Context, err error, point string) *Observation {
	state := "LIVE"
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		state = "DEADLINE"
	} else if ctx.Err() != nil {
		state = "CANCELLED"
	}
	stop := "NONE"
	if record.result.LocalStop != nil {
		stop = record.result.LocalStop.Source
	}
	reference, _ := ctx.Value(bootstrapKey{}).(bootstrapReference)
	if reference.owner != record {
		reference.tag = ""
	}
	return &Observation{BootstrapExchangeTag: reference.tag, Point: point, ErrorCategory: causeCode(err), ContextState: state,
		StopAtObservation: stop, ElapsedMS: time.Since(record.started).Milliseconds()}
}

func (record *recorder) failure(ctx context.Context, stage string, err error) {
	if err == nil || record.result.Complete || record.result.Status != "RUNNING" {
		return
	}
	record.result.Stage, record.result.Cause = stageCode(stage), causeCode(err)
	record.result.Observation = record.facts(ctx, err, "STARTUP_CALLER")
	if record.observation != nil && errors.Is(err, record.observedError) {
		record.result.Observation = record.observation
	}
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
		record.failure(ctx, stage, err)
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
		record.failure(ctx, "STARTUP", err)
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
		result.BootstrapExchanges = append([]BootstrapExchange(nil), result.BootstrapExchanges...)
		if result.Observation != nil {
			copy := *result.Observation
			result.Observation = &copy
		}
		if result.LocalStop != nil {
			copy := *result.LocalStop
			result.LocalStop = &copy
		}
		return &result
	}
	return nil
}

func Directory(ctx context.Context, encoded []byte) {
	if record := get(ctx); record != nil {
		digest := sha256.Sum256(encoded)
		record.mu.Lock()
		defer record.mu.Unlock()
		if !record.result.Complete && record.result.DirectoryFingerprint == "" {
			record.result.DirectoryFingerprint = hex.EncodeToString(digest[:])
		}
	}
}
