package bootstrap

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
)

type fidelityDeadline struct {
	context.Context
	bound time.Time
}

func (ctx fidelityDeadline) Deadline() (time.Time, bool) { return ctx.bound, true }

func TestFidelityReceive(test *testing.T) {
	for _, scenario := range []string{"io_deadline", "parent_deadline", "cancel", "peer_close", "invalid_hello", "success"} {
		test.Run(scenario, func(test *testing.T) {
			parent, finish := context.WithTimeout(context.Background(), 5*time.Second)
			defer finish()
			attempt, cancel := context.WithCancel(parent)
			defer cancel()
			client, server, _ := reproFamily(test, parent)
			if scenario == "io_deadline" {
				attempt = fidelityDeadline{Context: attempt, bound: time.Now().Add(150 * time.Millisecond)}
			}
			if scenario == "parent_deadline" {
				var expire context.CancelFunc
				attempt, expire = context.WithTimeout(attempt, 150*time.Millisecond)
				defer expire()
			}
			attempt = startupdiag.Start(attempt, 1)
			endpoint := &reproEndpoint{PacketEndpoint: client, result: make(chan map[string]any, 1)}
			done := make(chan error, 1)
			go func() { _, err := requestTransport(attempt, endpoint); done <- err }()
			reproReadBlocked(test, parent)
			var exchange chan error
			switch scenario {
			case "cancel":
				cancel()
			case "peer_close":
				server.Close()
			case "invalid_hello":
				if err := server.SendContext(parent, []byte(`{"type":"INVALID"}`)); err != nil {
					test.Fatal(err)
				}
			case "success":
				broker, _ := reproBroker(test)
				exchange = make(chan error, 1)
				go func() { exchange <- Exchange(attempt, server, broker, allow) }()
			}
			err := reproAwait(test, parent, done)
			actual := reproAwait(test, parent, endpoint.result)
			before := startupdiag.Snapshot(attempt)
			startupdiag.Complete(attempt, err)
			cancel()
			startupdiag.Cancel(attempt)
			startupdiag.Complete(attempt, context.Canceled)
			after := startupdiag.Snapshot(attempt)
			reproLog(test, "fidelity", map[string]any{"scenario": scenario, "actual_recv": actual, "before_cleanup": before, "after_cleanup": after})
			if scenario == "success" {
				if err != nil || after.Status != "SUCCEEDED" {
					test.Fatal("late stop replaced success")
				}
				if err := reproAwait(test, parent, exchange); err != nil {
					test.Fatal(err)
				}
				return
			}
			if startupdiag.Legacy(err) != roombroker.Code("bootstrap_protocol_rejected") {
				test.Fatal("legacy error changed")
			}
			want := "UNKNOWN"
			switch {
			case scenario == "invalid_hello":
				want = "PROTOCOL_REJECTED"
			case errors.Is(err, os.ErrDeadlineExceeded):
				want = "IO_DEADLINE"
			case errors.Is(err, context.DeadlineExceeded):
				want = "DEADLINE"
			case errors.Is(err, context.Canceled):
				want = "CANCELLED"
			case errors.Is(err, io.ErrClosedPipe):
				want = "CLOSED_PIPE"
			case errors.Is(err, io.EOF), errors.Is(err, io.ErrUnexpectedEOF):
				want = "EOF"
			}
			if scenario == "io_deadline" && (!errors.Is(err, os.ErrDeadlineExceeded) || actual["ctx_canceled"] != false || actual["ctx_deadline"] != false) {
				test.Fatal("not a live-context I/O deadline")
			}
			if before.Cause != want || after.Cause != want || before.Stage != "HELLO_RECEIVE" {
				test.Errorf("cause fidelity lost: want %s", want)
			}
			raw, _ := json.Marshal(after)
			var fields map[string]json.RawMessage
			json.Unmarshal(raw, &fields)
			var observed map[string]any
			json.Unmarshal(fields["observation"], &observed)
			point := "FAMILY_RECEIVE"
			if scenario == "invalid_hello" {
				point = "STARTUP_CALLER"
			}
			if observed["point"] != point {
				test.Errorf("first observation missing: %v", observed)
			}
			if (scenario == "peer_close" || scenario == "io_deadline" || scenario == "invalid_hello") && observed["context_state"] != "LIVE" {
				test.Error("late cancellation contaminated observation")
			}
		})
	}
}
