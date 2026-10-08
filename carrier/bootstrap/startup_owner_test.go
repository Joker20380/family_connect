//go:build fc_owner_diagnostic

package bootstrap

import (
	"context"
	"errors"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
	"testing"
)

func TestEarlyPrimaryBeforeDescriptorAndAfterCleanup(test *testing.T) {
	ctx := startupdiag.Start(sessiontrace.Watch(context.Background()), 2)
	_, err := requestTransport(ctx, primaryErrorEndpoint{failure: context.DeadlineExceeded})
	startupdiag.Cancel(ctx)
	startupdiag.Complete(ctx, err)
	result := startupdiag.Snapshot(ctx)
	if result.Attempt != 2 || result.Stage != "HELLO_RECEIVE" || result.Cause != "DEADLINE" || !result.Complete || sessiontrace.From(ctx) != nil || !errors.Is(err, context.DeadlineExceeded) {
		test.Fatalf("early cause lost: %+v", result)
	}
}
