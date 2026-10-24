package materials

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"net"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

func TestRelayChild(test *testing.T) {
	mode := os.Args[len(os.Args)-1]
	if !strings.HasPrefix(mode, "fc-relay-test-") {
		return
	}
	if mode == "fc-relay-test-block" {
		time.Sleep(30 * time.Second)
		os.Exit(0)
	}
	for identifier := uint64(1); identifier <= 2; identifier++ {
		var request struct {
			Schema int    `json:"schema"`
			ID     uint64 `json:"id"`
			Index  int    `json:"underlying_index"`
			Budget int64  `json:"budget_ms"`
			Path   string `json:"path"`
			Body   []byte `json:"body"`
		}
		if worker.ReadControlRequest(os.Stdin, &request) != nil || request.Schema != 1 || request.ID != identifier || request.Index != 2 || request.Budget <= 0 || request.Budget > 200000 {
			os.Exit(65)
		}
		response := map[string]any{"schema": 1, "id": identifier, "code": "OK"}
		envelope, _ := json.Marshal(map[string]any{"status": 200, "body": base64.StdEncoding.EncodeToString(request.Body)})
		response["body"] = envelope
		if mode == "fc-relay-test-unavailable" {
			response["code"] = "UNAVAILABLE"
			delete(response, "body")
		}
		if mode == "fc-relay-test-wrong-id" {
			response["id"] = identifier + 1
		}
		if worker.WriteControlReply(os.Stdout, response) != nil {
			os.Exit(65)
		}
		if mode != "fc-relay-test-ok" {
			os.Exit(0)
		}
	}
	os.Exit(0)
}

func testRelay(test *testing.T, mode string, budget time.Duration) (*relayProcess, context.Context) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), budget)
	relay := &relayProcess{ctx: ctx, cancel: cancel, index: 2, command: func(ctx context.Context) *exec.Cmd {
		return exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRelayChild$", "--", "fc-relay-test-"+mode)
	}}
	test.Cleanup(func() { relay.Close() })
	return relay, ctx
}

func TestRelayProcessKeepsOneSessionAndBoundsFrames(test *testing.T) {
	scratch := test.TempDir()
	test.Setenv("TMPDIR", scratch)
	process, ctx := testRelay(test, "ok", 3*time.Second)
	relay, _ := desktopmesh.NewReadinessRelay(process.request)
	for _, path := range []string{"/friends/restricted-readiness/challenge", "/friends/restricted-readiness"} {
		raw, err := relay.Post(ctx, path, []byte(`{"test_only":true}`), strings.Repeat("a", 32))
		if err != nil || string(raw) != `{"test_only":true}` {
			test.Fatal("relay pipe exchange failed", err)
		}
	}
	if process.identifier != 2 || process.Close() != nil || process.process != nil {
		test.Fatal("relay process not reaped")
	}
	entries, err := os.ReadDir(scratch)
	if err != nil || len(entries) != 0 {
		test.Fatal("relay private scratch survived close", err)
	}
}

func TestRelayProcessUnavailableIsNotProtocolOrAuthorizationFallback(test *testing.T) {
	for _, mode := range []string{"unavailable", "wrong-id"} {
		process, ctx := testRelay(test, mode, 3*time.Second)
		_, err := process.request(ctx, "/friends/restricted-readiness/challenge", []byte("{}"))
		var failure *desktopmesh.ReadinessFailure
		if !errors.As(err, &failure) || failure.Availability != (mode == "unavailable") || failure.Authorization || failure.Network {
			test.Fatal("relay status classification failed", mode, err)
		}
	}
}

func TestRelayProcessBlockedReadIsCancelledAndReaped(test *testing.T) {
	process, ctx := testRelay(test, "block", 80*time.Millisecond)
	started := time.Now()
	if _, err := process.request(ctx, "/friends/restricted-readiness/challenge", []byte("{}")); !errors.Is(err, context.DeadlineExceeded) {
		test.Fatal("blocked RNS read ignored deadline", err)
	}
	if process.Close() != nil || time.Since(started) > 2*time.Second {
		test.Fatal("RNS child survived timeout")
	}
}

func TestPreparationStartsRelayOnlyForChallengeNetworkFailure(test *testing.T) {
	for _, failure := range []*desktopmesh.ReadinessFailure{
		{Code: "CHALLENGE_TIMEOUT", Availability: true, Network: true},
		{Code: "TLS_TRUST_REJECTED"},
		{Code: "CHALLENGE_UNAUTHORIZED", Authorization: true},
		{Code: "CHALLENGE_UNAVAILABLE", Availability: true},
	} {
		test.Run(failure.Code, func(test *testing.T) {
			started := 0
			environment := preparationEnvironment{
				lookup: func(int) (*net.Interface, error) {
					return &net.Interface{Index: 2, Name: "synthetic", Flags: net.FlagUp}, nil
				},
				open: func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error) {
					return testPost(func(context.Context, string, []byte, string) ([]byte, error) {
						return nil, failure
					}), func() {}, nil
				},
				relay: func(ctx context.Context, index int) *relayProcess {
					ctx, cancel := context.WithCancel(ctx)
					return &relayProcess{ctx: ctx, cancel: cancel, index: index, command: func(ctx context.Context) *exec.Cmd {
						started++
						return exec.CommandContext(ctx, os.Args[0], "-test.run=^TestRelayChild$", "--", "fc-relay-test-unavailable")
					}}
				},
			}
			command := refreshCommand()
			command.BudgetMS = 3000
			reply := prepare(context.Background(), &command, &neverProtect{}, environment)
			if reply.OK || reply.Validated || !reply.RelayAvailable || (started == 1) != failure.Network || started > 1 {
				test.Fatal("unexpected relay fallback", reply.Code, started)
			}
		})
	}
}
