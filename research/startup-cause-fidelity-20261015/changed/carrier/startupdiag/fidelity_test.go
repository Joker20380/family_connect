package startupdiag

import (
	"context"
	"crypto/x509"
	"errors"
	"fmt"
	"io"
	"os"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type fidelityTimeout struct{}

func (fidelityTimeout) Error() string { return "not exported" }
func (fidelityTimeout) Timeout() bool { return true }

func TestFidelityCategoriesAndFirstFailure(test *testing.T) {
	for _, item := range []struct {
		err      error
		category string
	}{
		{fmt.Errorf("private: %w", os.ErrDeadlineExceeded), "IO_DEADLINE"},
		{context.DeadlineExceeded, "DEADLINE"}, {context.Canceled, "CANCELLED"},
		{fidelityTimeout{}, "TIMEOUT_UNQUALIFIED"}, {io.ErrClosedPipe, "CLOSED_PIPE"},
		{io.EOF, "EOF"}, {x509.UnknownAuthorityError{}, "CERTIFICATE_AUTHORITY"},
		{x509.CertificateInvalidError{Reason: x509.Expired}, "CERTIFICATE_TIME_INVALID"},
		{roombroker.Code("credentials_rejected"), "CREDENTIALS_REJECTED"},
		{roombroker.Code("bootstrap_protocol_rejected"), "PROTOCOL_REJECTED"},
		{errors.New("private"), "UNKNOWN"},
	} {
		ctx, cancel := context.WithCancel(context.Background())
		ctx = Start(ctx, 1)
		Failure(ctx, "FAMILY_AUTH", item.err)
		Stop(ctx, "CLEANUP")
		cancel()
		Cancel(ctx)
		Complete(ctx, item.err)
		result := Snapshot(ctx)
		if result.Cause != item.category || result.Stage != "FAMILY_AUTH" || result.Observation.ContextState != "LIVE" || result.Observation.StopAtObservation != "NONE" || result.LocalStop.Source != "CLEANUP" {
			test.Fatalf("first facts changed: %+v", result)
		}
		result.Observation.ContextState = "mutated"
		if Snapshot(ctx).Observation.ContextState != "LIVE" {
			test.Fatal("snapshot aliases recorder")
		}
	}
}

type fidelitySession struct{}

func (*fidelitySession) Close()       {}
func (*fidelitySession) Failed() bool { return false }

func TestFidelityOwnershipDrainStop(test *testing.T) {
	for _, source := range []string{"STARTUP_BUDGET", "CONNECT_CANCEL", "CLEANUP"} {
		test.Run(source, func(test *testing.T) {
			var coordinator restrictedowner.Coordinator
			cleanup := make(chan struct{})
			entered := make(chan struct{})
			chat, err := coordinator.AcquireChat(time.Now().Add(time.Minute), [32]byte{}, func(context.Context) (restrictedowner.Session, func(), error) {
				return &fidelitySession{}, func() { close(entered); <-cleanup }, nil
			}, func() {})
			if err != nil {
				test.Fatal(err)
			}
			if _, err = chat.Session(context.Background()); err != nil {
				test.Fatal(err)
			}
			parent, cancel := context.WithCancel(context.Background())
			ctx := Start(parent, 1)
			vpn, err := coordinator.ReserveVPN(ctx)
			if err != nil {
				test.Fatal(err)
			}
			<-entered
			if source == "STARTUP_BUDGET" {
				defer StartBudget(ctx, 20*time.Millisecond, cancel)()
			} else {
				if source == "CLEANUP" {
					Failure(ctx, "OWNERSHIP_DRAIN", errors.New("unknown drain failure"))
				}
				Stop(ctx, source)
				cancel()
			}
			err = vpn.Wait(ctx)
			Failure(ctx, "OWNERSHIP_DRAIN", err)
			Stop(ctx, "CLEANUP")
			cancel()
			Complete(ctx, err)
			result := Snapshot(ctx)
			if result.Stage != "OWNERSHIP_DRAIN" || result.LocalStop.Source != source {
				test.Fatalf("wrong drain attribution: %+v", result)
			}
			if source == "CLEANUP" {
				if result.Cause != "UNKNOWN" || result.Observation.ContextState != "LIVE" {
					test.Fatal("cleanup became cause")
				}
			} else if result.Cause != "CANCELLED" || result.Observation.StopAtObservation != source {
				test.Fatal("budget cancel reclassified runtime error")
			}
			close(cleanup)
			vpn.Release()
			chat.Release()
			test.Logf("stage=%s error=%s local_stop=%s observed_context=%s", result.Stage, result.Cause, result.LocalStop.Source, result.Observation.ContextState)
		})
	}
}

func TestFidelityBudgetSuccessAndGeneration(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	ctx = Start(ctx, 1)
	stop := StartBudget(ctx, 20*time.Millisecond, cancel)
	if !stop() {
		test.Fatal("timer already fired")
	}
	Complete(ctx, nil)
	old, oldCancel := context.WithCancel(context.Background())
	old = Start(old, 2)
	StartBudget(old, 20*time.Millisecond, oldCancel)
	select {
	case <-old.Done():
	case <-time.After(time.Second):
		test.Fatal("old timer did not fire")
	}
	if ctx.Err() != nil || Snapshot(ctx).Status != "SUCCEEDED" || Snapshot(ctx).LocalStop != nil {
		test.Fatal("stopped/old timer killed successful generation")
	}
	Stop(ctx, "CONNECT_CANCEL")
	cancel()
	Cancel(ctx)
	Complete(ctx, context.Canceled)
	if Snapshot(ctx).Status != "SUCCEEDED" || Snapshot(ctx).Observation != nil {
		test.Fatal("late stop created failure")
	}
}
