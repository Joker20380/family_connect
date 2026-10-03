package sessiondiag

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

func TestReasonTypedAndNeverRaw(test *testing.T) {
	for _, row := range []struct {
		err  error
		want string
	}{
		{nil, "NONE"}, {context.Canceled, "CANCELLED"}, {context.DeadlineExceeded, "DEADLINE"},
		{io.EOF, "EOF"}, {io.ErrUnexpectedEOF, "EOF"}, {io.ErrClosedPipe, "IO_CLOSED"},
		{net.ErrClosed, "IO_CLOSED"}, {familysession.ErrRejected, "FAMILY_REJECTED"},
		{tcpforward.ErrProtocol, "MUX_PROTOCOL"}, {reliablestream.ErrProtocol, "RELIABLE_PROTOCOL"},
		{reliablestream.ErrExhausted, "RELIABLE_EXHAUSTED"}, {reliablestream.ErrReset, "REMOTE_RESET"},
		{reliablestream.ErrClosed, "RELIABLE_CLOSED"}, {errors.New("private destination/token"), "UNKNOWN"},
		{&net.DNSError{Err: "private resolver", IsTimeout: true}, "NETWORK_TIMEOUT"},
		{&net.OpError{Op: "private", Err: errors.New("private address")}, "NETWORK_ERROR"},
	} {
		if got := Reason(row.err); got != row.want {
			test.Fatalf("got %s want %s", got, row.want)
		}
		if row.err != nil && Reason(fmt.Errorf("private wrapper: %w", row.err)) != row.want {
			test.Fatal("wrapped classification")
		}
	}
}

func TestCaptureBoundedProjectionAndCorrelation(test *testing.T) {
	setup := strings.Repeat("0123456789abcdef", 4)
	reliable := reliablestream.Stats{Terminal: "recovery_exhausted", Retransmissions: 8, Timeouts: 3}
	media := telemost.Stats{SubscriberState: "private address", PublisherState: "connected", EvidenceDropped: 4,
		Evidence: []telemost.Evidence{{Stage: "ICE_SELECTED_PAIR", LocalType: "private candidate"},
			{Stage: "CONNECTION_STATE", Target: "SUBSCRIBER", State: "disconnected"},
			{Stage: "WS_FAIL", State: "close_code_1006", ReasonKeywords: []string{"private token"}}}}
	when := time.Unix(1791043460, 0)
	report := Capture(setup, io.ErrClosedPipe, when, reliable, media, tcpforward.MuxStats{DNSResponses: 4, OpenOK: 2})
	if report.SessionTag == setup || len(report.SessionTag) != 64 || report.TerminalAtMS != when.UnixMilli() {
		test.Fatal("correlation/time")
	}
	if report.SessionTag != Capture(setup, nil, time.Time{}, reliable, media, tcpforward.MuxStats{}).SessionTag {
		test.Fatal("unstable correlation")
	}
	if report.ICEFailure != "SUBSCRIBER_disconnected" || report.SignalingFailure != "close_code_1006" || report.ReliableTerminal != "recovery_exhausted" {
		test.Fatal("lost layer evidence")
	}
	raw, err := json.Marshal(report)
	if err != nil || len(raw) > 2048 || strings.Contains(string(raw), "private") || strings.Contains(string(raw), setup) {
		test.Fatal("unsafe projection")
	}
	media.Evidence = []telemost.Evidence{{Stage: "WS_FAIL", State: "private server error"}, {Stage: "CONNECTION_STATE", Target: "private", State: "failed"}}
	reliable.Terminal = "private error"
	report = Capture("private setup", errors.New("private failure"), time.Time{}, reliable, media, tcpforward.MuxStats{})
	if report.SessionTag != "" || report.TerminalReason != "UNKNOWN" || report.TerminalAtMS != 0 || report.SignalingFailure != "UNKNOWN" || report.ICEFailure != "UNKNOWN" || report.ReliableTerminal != "UNKNOWN" {
		test.Fatal("untrusted fields passed through")
	}
}
