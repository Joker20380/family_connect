package familysession

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestStopSourceDistinguishesCredentialExpiryAndParent(test *testing.T) {
	cancelled, cancel := context.WithCancel(context.Background())
	cancel()
	for _, item := range []struct {
		name   string
		ctx    context.Context
		expiry time.Time
		want   string
	}{
		{"credential", context.Background(), time.Now().Add(-time.Second), "FAMILY_CREDENTIAL_EXPIRY"},
		{"parent", cancelled, time.Now().Add(time.Minute), "PARENT_CANCELLED"},
		{"read", context.Background(), time.Now().Add(time.Minute), "FAMILY_READ"},
	} {
		test.Run(item.name, func(test *testing.T) {
			trace := sessiontrace.New(strings.Repeat("a", 64), nil)
			session := &Session{trace: trace, expiry: item.expiry}
			session.traceStop(item.ctx, "FAMILY_READ")
			trace.Add("LOCAL_CLOSE", "STARTED", "NONE")
			if trace.Snapshot().FirstClose.CloseSource != item.want {
				test.Fatal(trace.Snapshot().FirstClose)
			}
		})
	}
}
