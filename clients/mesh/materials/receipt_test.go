package materials

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"net"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
)

func receiptCommand() Command {
	command := refreshCommand()
	command.Action, command.UnderlyingIndex, command.BudgetMS, command.Required = "receipt", 0, 0, false
	command.Phase, command.AppVersion, command.VersionCode = "restart", "linux-0.2.11", 2011
	return command
}

func TestReceiptCommandEvaluatesDurableStateOffline(test *testing.T) {
	command := receiptCommand()
	platform := &neverProtect{}
	reply := Prepare(context.Background(), &command, platform)
	if !reply.OK || reply.Code != "RECEIPT_READY" || reply.Receipt == nil || reply.Receipt.Result != desktopmesh.ReadinessMissing || reply.Durable || reply.Validated || platform.calls != 0 {
		test.Fatal("offline receipt is not a missing-state observation")
	}
	command.Cached = json.RawMessage(`{"response":null,"denied":true,"next_attempt":0,"receipt_context":{"challenge_id":"cccccccccccccccccccccccccccccccc","fetch_id":"dddddddddddddddddddddddddddddddd"}}`)
	reply = Prepare(context.Background(), &command, platform)
	if !reply.OK || reply.Receipt.Result != desktopmesh.ReadinessDenied || reply.Receipt.Correlation != strings.Repeat("c", 32) {
		test.Fatal("restart did not use stored denial/context")
	}
	command.Phase, command.ImportResult = "import", "FETCH_FAILED"
	reply = Prepare(context.Background(), &command, platform)
	if !reply.OK || reply.Receipt.Result != "FETCH_FAILED" || reply.Receipt.Correlation != command.Attempt.ChallengeID || reply.Receipt.Usable {
		test.Fatal("failed refresh reported cached state as imported")
	}
}

func TestReceiptValidationPrecedesNetworking(test *testing.T) {
	for _, change := range []func(*Command){func(command *Command) { command.AppVersion = "private token" },
		func(command *Command) { command.VersionCode = 0 }, func(command *Command) { command.Phase = "other" },
		func(command *Command) { command.ImportResult = "READY" }, func(command *Command) { command.UnderlyingIndex = 2 },
		func(command *Command) { command.Receipt = json.RawMessage(`{}`) }} {
		command := receiptCommand()
		change(&command)
		reply := Prepare(context.Background(), &command, &neverProtect{})
		if reply.OK || reply.Code != "INVALID_MATERIALS_COMMAND" {
			test.Fatal("invalid receipt command accepted")
		}
	}
}

func TestAckCommandBindsOwnProofAndReceipt(test *testing.T) {
	command := receiptCommand()
	receipt, err := desktopmesh.FailureReadinessReceipt(*command.Attempt, time.Now(), "import", command.AppVersion, command.VersionCode, "FETCH_FAILED")
	if err != nil {
		test.Fatal(err)
	}
	command.Receipt, _ = json.Marshal(receipt)
	command.Action, command.Attempt, command.Cached = "ack", nil, nil
	command.Phase, command.AppVersion, command.VersionCode = "", "", 0
	command.UnderlyingIndex, command.BudgetMS = 2, 15000
	calls, closed := 0, false
	environment := preparationEnvironment{lookup: func(int) (*net.Interface, error) {
		return &net.Interface{Index: 2, Name: "synthetic", Flags: net.FlagUp}, nil
	}, open: func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error) {
		return testPost(func(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
			calls++
			var request map[string]json.RawMessage
			if json.Unmarshal(body, &request) != nil || string(request["receipt"]) != string(command.Receipt) {
				test.Fatal("ack payload changed")
			}
			if strings.HasSuffix(path, "ack-challenge") {
				challenge, _ := json.Marshal(map[string]any{"challenge": base64.StdEncoding.EncodeToString(make([]byte, 32)),
					"expires_at": time.Now().Unix() + 60, "audience": "family-connect/enrollment/v1"})
				return challenge, nil
			}
			if path != "/friends/restricted-readiness/ack" || request["proof"] == nil {
				test.Fatal("ack did not use its own proof exchange")
			}
			return []byte(`{"version":1,"correlation_id":"` + receipt.Correlation + `","status":"ACK_RECEIVED"}`), nil
		}), func() { closed = true }, nil
	}}
	reply := prepare(context.Background(), &command, &neverProtect{}, environment)
	if !reply.OK || reply.Code != "ACK_RECEIVED" || reply.Durable || reply.Validated || reply.StorageRequired || calls != 2 || !closed {
		test.Fatal("ack did not complete bounded transport exchange", reply.Code)
	}
	command.BudgetMS = 15001
	if valid(&command) {
		test.Fatal("unbounded ack accepted")
	}
	command.BudgetMS = 15000
	command.Receipt = json.RawMessage(`{}`)
	if valid(&command) {
		test.Fatal("invalid ack payload accepted")
	}
}
