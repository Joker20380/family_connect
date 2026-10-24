package materials

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type neverProtect struct{ calls int }

func (platform *neverProtect) Protect(net.Interface, int) bool {
	platform.calls++
	return false
}

func inspectCommand() Command {
	return Command{Schema: 1, ID: 1, Action: "inspect", Public: make([]byte, 64), Anchor: make([]byte, 32), Cached: json.RawMessage("null")}
}

func refreshCommand() Command {
	return Command{Schema: 1, ID: 1, Action: "refresh", Identity: make([]byte, 64), Wireguard: make([]byte, 32), Anchor: make([]byte, 32),
		Cached: json.RawMessage("null"), UnderlyingIndex: 2, BudgetMS: 1000, Required: true,
		Attempt: &desktopmesh.ReadinessAttempt{ChallengeID: strings.Repeat("a", 32), FetchID: strings.Repeat("b", 32)}}
}

func TestInspectIsOfflineAndNeverClaimsDurability(test *testing.T) {
	command := inspectCommand()
	platform := &neverProtect{}
	reply := Prepare(context.Background(), &command, platform)
	if !reply.OK || reply.Code != "MISSING" || reply.Validated || reply.Durable || reply.StorageRequired || reply.CacheProposal != nil || platform.calls != 0 {
		test.Fatal("missing offline state became usable or durable")
	}
	command.Cached = json.RawMessage(`{"response":null,"denied":true,"next_attempt":0}`)
	reply = Prepare(context.Background(), &command, platform)
	if !reply.OK || reply.Code != "AUTHORIZATION_REJECTED" || reply.Validated || reply.CacheProposal != nil {
		test.Fatal("denied state became usable")
	}
	command.Cached = json.RawMessage(`{"response":null,"denied":false,"denied":true,"next_attempt":0}`)
	reply = Prepare(context.Background(), &command, platform)
	if reply.Code != "PERSISTENCE_FAILED" || reply.Validated {
		test.Fatal("ambiguous cache accepted")
	}
}

func TestMaterialsValidationBeforeAnyUnderlay(test *testing.T) {
	for _, change := range []func(*Command){func(command *Command) { command.Action = "exec" },
		func(command *Command) { command.ID = 0 }, func(command *Command) { command.Schema = 2 },
		func(command *Command) { command.Identity = []byte("secret") }, func(command *Command) { command.BudgetMS = 200001 },
		func(command *Command) { command.UnderlyingIndex = 0 }, func(command *Command) { command.Attempt.ChallengeID = "bad" },
		func(command *Command) { command.Cached = bytes.Repeat([]byte("x"), desktopmesh.MaxReadinessCache+1) }} {
		command := refreshCommand()
		change(&command)
		platform := &neverProtect{}
		reply := Prepare(context.Background(), &command, platform)
		if reply.OK || reply.Code != "INVALID_MATERIALS_COMMAND" || platform.calls != 0 {
			test.Fatal("invalid input reached networking")
		}
	}
	if reply := Prepare(context.Background(), nil, &neverProtect{}); reply.OK {
		test.Fatal("nil command accepted")
	}
}

type testPost func(context.Context, string, []byte, string) ([]byte, error)

func (post testPost) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	return post(ctx, path, body, probe)
}

func TestAuthorizationDenialReturnsMandatoryPrivateStorageProposal(test *testing.T) {
	command := refreshCommand()
	closed, calls := false, 0
	environment := preparationEnvironment{lookup: func(int) (*net.Interface, error) {
		return &net.Interface{Index: 2, Name: "synthetic", Flags: net.FlagUp}, nil
	}, open: func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error) {
		return testPost(func(context.Context, string, []byte, string) ([]byte, error) {
			calls++
			return nil, &desktopmesh.ReadinessFailure{Code: "CHALLENGE_UNAUTHORIZED", Authorization: true}
		}), func() { closed = true }, nil
	}}
	reply := prepare(context.Background(), &command, &neverProtect{}, environment)
	if reply.OK || reply.Validated || reply.Durable || !reply.StorageRequired || reply.Code != "AUTHORIZATION_REJECTED" || !closed || calls != 1 {
		test.Fatal("denial persistence proposal missing")
	}
	var stored struct {
		Denied bool `json:"denied"`
	}
	if json.Unmarshal(reply.CacheProposal, &stored) != nil || !stored.Denied {
		test.Fatal("deny latch not in proposal")
	}
	digest := sha256.Sum256(reply.CacheProposal)
	if reply.CandidateSHA256 != hex.EncodeToString(digest[:]) {
		test.Fatal("proposal digest mismatch")
	}
	if strings.Contains(fmt.Sprintf("%+v %#v", command, reply), "denied") {
		test.Fatal("private proposal leaked through formatting")
	}
}

func TestMaterialsFramingAndSingleOperation(test *testing.T) {
	command := inspectCommand()
	raw, _ := json.Marshal(command)
	var input, output bytes.Buffer
	binary.Write(&input, binary.BigEndian, uint32(len(raw)))
	input.Write(raw)
	if err := Serve(context.Background(), &input, &output, &neverProtect{}); err != nil {
		test.Fatal(err)
	}
	var size uint32
	if binary.Read(&output, binary.BigEndian, &size) != nil || int(size) != output.Len() || size > worker.MaxReply {
		test.Fatal("invalid response frame")
	}
	var reply Reply
	if json.Unmarshal(output.Bytes(), &reply) != nil || reply.Code != "MISSING" || reply.Durable || reply.Validated {
		test.Fatal("offline command response invalid")
	}
	for _, raw := range []string{`{"schema":1,"id":1,"id":2,"action":"inspect"}`, `{"schema":1,"id":1,"action":"inspect","path":"/etc/shadow"}`,
		`{"schema":1,"id":1,"action":"inspect","cached":{"bad":"` + string([]byte{0xff}) + `"}}`} {
		input.Reset()
		output.Reset()
		binary.Write(&input, binary.BigEndian, uint32(len(raw)))
		input.WriteString(raw)
		if err := Serve(context.Background(), &input, &output, &neverProtect{}); err == nil || output.Len() != 0 {
			test.Fatal("invalid framing command accepted")
		}
	}
}

func TestMaterialsCancelCannotReturnReadyOrStartNetworking(test *testing.T) {
	command := refreshCommand()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	platform := &neverProtect{}
	reply := Prepare(ctx, &command, platform)
	if reply.OK || reply.Validated || reply.Code != "CANCELLED" || platform.calls != 0 {
		test.Fatal("cancellation ignored")
	}
}
