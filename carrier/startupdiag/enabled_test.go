//go:build fc_owner_diagnostic

package startupdiag

import (
	"context"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

func TestPrimaryBeforeCleanupCancellationAndCompletion(test *testing.T) {
	ctx := Start(context.Background(), 1)
	Failure(ctx, "HELLO_RECEIVE", context.DeadlineExceeded)
	before := *Snapshot(ctx)
	Cancel(ctx)
	Failure(ctx, "DEDICATED_BIND", errors.New("cleanup secret"))
	Complete(ctx, context.Canceled)
	after := Snapshot(ctx)
	if after.Stage != before.Stage || after.Cause != "DEADLINE" || after.Status != "FAILED" || !after.Complete || after.ObservedMS != before.ObservedMS || after.CompletedMS < after.ObservedMS {
		test.Fatal("primary changed", after)
	}
	Complete(ctx, nil)
	if *Snapshot(ctx) != *after {
		test.Fatal("completion was not immutable")
	}
}

func TestControlledConcurrentPublicationOrders(test *testing.T) {
	for _, first := range []string{"failure", "cancel", "success"} {
		test.Run(first, func(test *testing.T) {
			ctx := Start(context.Background(), 2)
			published := make(chan struct{})
			finished := make(chan struct{})
			go func() {
				switch first {
				case "failure":
					Failure(ctx, "SEED_CONNECT", context.DeadlineExceeded)
				case "cancel":
					Cancel(ctx)
				case "success":
					Complete(ctx, nil)
				}
				close(published)
			}()
			go func() {
				<-published
				Failure(ctx, "HELLO_RECEIVE", errors.New("late secret"))
				Cancel(ctx)
				Complete(ctx, context.Canceled)
				close(finished)
			}()
			<-finished
			expected := map[string]string{"failure": "DEADLINE", "cancel": "CANCELLED", "success": "NONE"}[first]
			if result := Snapshot(ctx); result.Cause != expected || !result.Complete {
				test.Fatal(result)
			}
		})
	}
}

func TestIndependentAttemptsAndRetention(test *testing.T) {
	first := Start(context.Background(), 1)
	Complete(first, nil)
	second := Start(context.Background(), 2)
	Failure(second, "FAMILY_AUTH", familysession.ErrRejected)
	Complete(second, familysession.ErrRejected)
	third := Start(context.Background(), 3)
	Complete(third, nil)
	Failure(first, "SEED_CONNECT", context.DeadlineExceeded)
	Cancel(second)
	if Snapshot(first).Status != "SUCCEEDED" || Snapshot(second).Attempt != 2 || Snapshot(second).Stage != "FAMILY_AUTH" || Snapshot(second).Cause != "UNKNOWN" || Snapshot(third).Status != "SUCCEEDED" {
		test.Fatal("attempts mixed")
	}
	for index := 0; index < 512; index++ {
		if Snapshot(second).Cause != "UNKNOWN" {
			test.Fatal("read consumed terminal cause")
		}
	}
}

func TestCauseAllowlistAndPrivacy(test *testing.T) {
	secret := "https://room.invalid/?token=private /private/profile password=secret SDP"
	for _, item := range []struct {
		failure error
		cause   string
	}{
		{context.DeadlineExceeded, "DEADLINE"}, {context.Canceled, "CANCELLED"},
		{x509.CertificateInvalidError{Reason: x509.Expired}, "CERTIFICATE_TIME_INVALID"},
		{x509.CertificateInvalidError{}, "CERTIFICATE_INVALID"}, {x509.UnknownAuthorityError{}, "CERTIFICATE_AUTHORITY"},
		{x509.HostnameError{}, "CERTIFICATE_HOSTNAME"}, {familysession.ErrRejected, "UNKNOWN"},
		{telemost.ErrAPI, "PROVIDER_API"}, {telemost.ErrClosed, "CARRIER_CLOSED"}, {io.EOF, "EOF"},
		{roombroker.Code("bootstrap_protocol_rejected"), "PROTOCOL_REJECTED"},
		{roombroker.Code("descriptor_expired"), "DESCRIPTOR_EXPIRED"},
		{roombroker.Code("bootstrap_connect_timeout"), "UNKNOWN"}, {errors.New(secret), "UNKNOWN"},
	} {
		ctx := Start(context.Background(), 1)
		Failure(ctx, "HELLO_RECEIVE", fmt.Errorf("%s: %w", secret, item.failure))
		Complete(ctx, item.failure)
		result := Snapshot(ctx)
		encoded, _ := json.Marshal(result)
		if result.Cause != item.cause || strings.Contains(string(encoded), "private") || strings.Contains(string(encoded), "password") {
			test.Fatalf("unsafe or incorrect classification: %s", encoded)
		}
	}
	ctx := Start(context.Background(), 2)
	Failure(ctx, secret, errors.New(secret))
	if Snapshot(ctx).Stage != "UNKNOWN" {
		test.Fatal("stage was not allowlisted")
	}
}
