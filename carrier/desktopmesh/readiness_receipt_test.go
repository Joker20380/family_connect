package desktopmesh

import (
	"bytes"
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func TestReceiptDecoderRequiresEveryTypedField(test *testing.T) {
	receipt, err := FailureReadinessReceipt(cacheAttempt(), time.Unix(200, 0), "import", "linux-0.2.11", 2011, "FETCH_FAILED")
	if err != nil {
		test.Fatal(err)
	}
	raw, _ := json.Marshal(receipt)
	if _, err := DecodeReadinessReceipt(raw); err != nil {
		test.Fatal(err)
	}
	var fields map[string]json.RawMessage
	json.Unmarshal(raw, &fields)
	for name, original := range fields {
		delete(fields, name)
		missing, _ := json.Marshal(fields)
		if _, err := DecodeReadinessReceipt(missing); err == nil {
			test.Fatal("missing receipt field accepted", name)
		}
		fields[name] = json.RawMessage("null")
		nullField, _ := json.Marshal(fields)
		if _, err := DecodeReadinessReceipt(nullField); err == nil {
			test.Fatal("null receipt field accepted", name)
		}
		fields[name] = original
	}
	for _, invalid := range [][]byte{bytes.Replace(raw, []byte(`"version":1`), []byte(`"version":1,"version":1`), 1),
		bytes.Replace(raw, []byte(`"orchestrator_usable":false`), []byte(`"orchestrator_usable":"false"`), 1),
		bytes.Repeat([]byte(" "), MaxReadinessReceipt+1)} {
		if _, err := DecodeReadinessReceipt(invalid); err == nil {
			test.Fatal("ambiguous or oversized receipt accepted")
		}
	}
	if _, err := FailureReadinessReceipt(cacheAttempt(), time.Unix(200, 0), "import", "linux-0.2.11", 2011, ReadinessReady); err == nil {
		test.Fatal("READY without verified material")
	}
}

func TestImportResultDoesNotClaimCacheFallbackIsFreshImport(test *testing.T) {
	cache := policyCache(test, &memoryReadiness{})
	if err := cache.Accept(policyMaterial(test), cacheAttempt(), time.Unix(200, 0)); err != nil {
		test.Fatal(err)
	}
	client := testReadinessClient(test)
	calls := 0
	transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
		calls++
		return nil, &ReadinessFailure{Code: "CHALLENGE_UNAVAILABLE", Availability: true}
	})
	raw, source, result, err := ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), true)
	if err != nil || source != ReadinessSaved || len(raw) == 0 || result != "FETCH_FAILED" || calls != 1 {
		test.Fatal("cached selection misreported as import success", err, result)
	}
	clear(raw)
	raw, _, result, err = ResolveReadinessWithResult(context.Background(), cache, client, transport, cacheAttempt(), false)
	clear(raw)
	if err != nil || result != "" || calls != 1 {
		test.Fatal("cooldown generated another import result", err, result)
	}
}

func TestReadinessReceiptSchemaAndRestartCorrelation(test *testing.T) {
	cache := policyCache(test, &memoryReadiness{})
	if err := cache.Accept(policyMaterial(test), cacheAttempt(), time.Unix(200, 0)); err != nil {
		test.Fatal(err)
	}
	attempt, _ := NewReadinessAttempt()
	receipt, err := cache.Receipt(attempt, time.Unix(201, 0), "restart", "0.0.0-test", 1)
	if err != nil || receipt.Correlation != cacheAttempt().ChallengeID || receipt.FetchID != cacheAttempt().FetchID || !receipt.Usable {
		test.Fatal("restart lost durable receipt context", err)
	}
	raw, _ := json.Marshal(receipt)
	var fields map[string]any
	json.Unmarshal(raw, &fields)
	if len(fields) != 17 || strings.Contains(string(raw), "certificate") || strings.Contains(string(raw), "synthetic") {
		test.Fatal("receipt leaked material or changed wire fields")
	}
	for _, change := range []func(*ReadinessReceipt){func(receipt *ReadinessReceipt) { receipt.Usable = false },
		func(receipt *ReadinessReceipt) { receipt.FetchID = receipt.ChallengeID }, func(receipt *ReadinessReceipt) { receipt.ExpiresAt = receipt.ObservedAt },
		func(receipt *ReadinessReceipt) { receipt.Failure = "secret" }, func(receipt *ReadinessReceipt) { receipt.Result = "UNKNOWN" },
		func(receipt *ReadinessReceipt) { receipt.Phase = "anything" }} {
		changed := receipt
		change(&changed)
		if changed.Validate() == nil {
			test.Fatal("invalid readiness receipt accepted")
		}
	}
	expired, err := cache.Receipt(attempt, time.Unix(1000, 0), "restart", "0.0.0-test", 1)
	if err != nil || expired.Usable || expired.Result != ReadinessExpired || expired.ExpiresAt != 0 {
		test.Fatal("expired receipt claims readiness")
	}
}

func TestReadinessAckUsesSeparateProofAndExactCorrelation(test *testing.T) {
	cache := policyCache(test, &memoryReadiness{})
	receipt, err := cache.Receipt(cacheAttempt(), time.Unix(200, 0), "import", "0.0.0-test", 1)
	if err != nil {
		test.Fatal(err)
	}
	client := testReadinessClient(test)
	for _, correlation := range []string{receipt.Correlation, strings.Repeat("f", 32)} {
		calls := 0
		transport := readinessPost(func(_ context.Context, path string, body []byte, probe string) ([]byte, error) {
			calls++
			if !validProbeID(probe) {
				test.Fatal("invalid probe ID")
			}
			var value map[string]json.RawMessage
			if json.Unmarshal(body, &value) != nil || value["receipt"] == nil {
				test.Fatal("receipt not bound to acknowledgment")
			}
			if path == "/friends/restricted-readiness/ack-challenge" {
				if value["public_identity"] == nil || value["wireguard_public_key"] == nil || len(value) != 3 {
					test.Fatal("ack challenge fields differ")
				}
				return []byte(`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":300,"audience":"family-connect/enrollment/v1"}`), nil
			}
			if path != "/friends/restricted-readiness/ack" || value["proof"] == nil || len(value) != 2 {
				test.Fatal("ack proof fields differ")
			}
			return []byte(`{"version":1,"correlation_id":"` + correlation + `","status":"ACK_RECEIVED"}`), nil
		})
		err := client.Acknowledge(context.Background(), transport, receipt)
		if (err == nil) != (correlation == receipt.Correlation) || calls != 2 {
			test.Fatal("ack correlation boundary failed")
		}
	}
}
