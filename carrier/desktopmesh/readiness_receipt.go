package desktopmesh

import (
	"bytes"
	"context"
	"encoding/json"
	"regexp"
	"strings"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type ReadinessReceipt struct {
	Version      int           `json:"version"`
	Type         string        `json:"type"`
	Correlation  string        `json:"correlation_id"`
	ChallengeID  string        `json:"challenge_id"`
	FetchID      string        `json:"fetch_id"`
	Result       ReadinessCode `json:"result"`
	Provisioning string        `json:"provisioning"`
	Bootstrap    string        `json:"bootstrap"`
	Usable       bool          `json:"orchestrator_usable"`
	Revision     int64         `json:"revision"`
	MinimumCRL   int64         `json:"minimum_crl"`
	ExpiresAt    int64         `json:"expires_at"`
	ObservedAt   int64         `json:"observed_at"`
	Phase        string        `json:"phase"`
	AppVersion   string        `json:"app_version"`
	VersionCode  int64         `json:"version_code"`
	Failure      string        `json:"failure_reason"`
}

var readinessAppVersion = regexp.MustCompile(`^[A-Za-z0-9._-]{1,64}$`)

const MaxReadinessReceipt = 4096

func DecodeReadinessReceipt(raw []byte) (ReadinessReceipt, error) {
	var receipt ReadinessReceipt
	var fields map[string]json.RawMessage
	if strictReadinessJSON(raw, MaxReadinessReceipt, &fields) != nil || len(fields) != 17 {
		return receipt, ErrConfiguration
	}
	for _, name := range strings.Fields("version type correlation_id challenge_id fetch_id result provisioning bootstrap orchestrator_usable revision minimum_crl expires_at observed_at phase app_version version_code failure_reason") {
		if fields[name] == nil || bytes.Equal(bytes.TrimSpace(fields[name]), []byte("null")) {
			return receipt, ErrConfiguration
		}
	}
	if strictReadinessJSON(raw, MaxReadinessReceipt, &receipt) != nil || receipt.Validate() != nil {
		return ReadinessReceipt{}, ErrConfiguration
	}
	return receipt, nil
}

func FailureReadinessReceipt(attempt ReadinessAttempt, now time.Time, phase, version string, build int64, code ReadinessCode) (ReadinessReceipt, error) {
	receipt := ReadinessReceipt{Version: 1, Type: "READINESS_IMPORT_RESULT", Correlation: attempt.ChallengeID,
		ChallengeID: attempt.ChallengeID, FetchID: attempt.FetchID, Result: code, Provisioning: "NOT_READY", Bootstrap: "NOT_READY",
		ObservedAt: now.Unix(), Phase: phase, AppVersion: version, VersionCode: build, Failure: string(code)}
	if receipt.Validate() != nil {
		return ReadinessReceipt{}, ErrConfiguration
	}
	return receipt, nil
}

func (receipt ReadinessReceipt) Validate() error {
	if receipt.Version != 1 || receipt.Type != "READINESS_IMPORT_RESULT" || receipt.Correlation != receipt.ChallengeID ||
		!(ReadinessAttempt{ChallengeID: receipt.ChallengeID, FetchID: receipt.FetchID}).Valid() ||
		(receipt.Phase != "import" && receipt.Phase != "restart") || !readinessAppVersion.MatchString(receipt.AppVersion) ||
		receipt.ObservedAt <= 0 || receipt.ObservedAt > maxReadinessInteger || receipt.VersionCode <= 0 || receipt.VersionCode > maxReadinessInteger {
		return ErrConfiguration
	}
	switch receipt.Result {
	case ReadinessReady, ReadinessMissing, ReadinessInvalid, ReadinessBootstrap, ReadinessExpired, ReadinessDenied, ReadinessStale, ReadinessPersistence,
		"ATOMIC_IMPORT_FAILED", "ORCHESTRATOR_NOT_USABLE", "INTERNAL_ERROR", "FETCH_FAILED":
	default:
		return ErrConfiguration
	}
	ready := receipt.Result == ReadinessReady
	state, failure := "NOT_READY", string(receipt.Result)
	minimum := int64(0)
	if ready {
		state, failure, minimum = "PRESENT_VALID", "NONE", 1
	}
	if receipt.Usable != ready || receipt.Provisioning != state || receipt.Bootstrap != state || receipt.Failure != failure {
		return ErrConfiguration
	}
	for _, value := range []int64{receipt.Revision, receipt.MinimumCRL, receipt.ExpiresAt} {
		if value < minimum || value > maxReadinessInteger {
			return ErrConfiguration
		}
	}
	if ready && receipt.ExpiresAt <= receipt.ObservedAt {
		return ErrConfiguration
	}
	return nil
}

func (cache *ReadinessCache) Receipt(attempt ReadinessAttempt, now time.Time, phase, version string, build int64) (ReadinessReceipt, error) {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	receipt := ReadinessReceipt{Version: 1, Type: "READINESS_IMPORT_RESULT", Result: ReadinessMissing,
		ObservedAt: now.Unix(), Phase: phase, AppVersion: version, VersionCode: build, Provisioning: "NOT_READY", Bootstrap: "NOT_READY"}
	state, err := cache.state()
	defer clear(state.Response)
	if state.Context != nil && phase == "restart" {
		attempt = *state.Context
	}
	receipt.ChallengeID, receipt.Correlation, receipt.FetchID = attempt.ChallengeID, attempt.ChallengeID, attempt.FetchID
	switch {
	case err != nil:
		receipt.Result = ReadinessPersistence
	case state.Denied:
		receipt.Result = ReadinessDenied
	case !absent(state.Response):
		receipt.Result = cache.validate(state.Response, now)
	}
	if receipt.Result == ReadinessReady {
		var delivery wholedevice.ReadinessDelivery
		if strictReadinessJSON(state.Response, wholedevice.MaxReadiness, &delivery) != nil {
			receipt.Result = ReadinessInvalid
		} else {
			receipt.Usable, receipt.Provisioning, receipt.Bootstrap = true, "PRESENT_VALID", "PRESENT_VALID"
			receipt.Revision, receipt.MinimumCRL, receipt.ExpiresAt = int64(delivery.Revision), delivery.MinimumCRL, delivery.ExpiresAt
		}
	}
	receipt.Failure = string(receipt.Result)
	if receipt.Usable {
		receipt.Failure = "NONE"
	}
	if err := receipt.Validate(); err != nil {
		return ReadinessReceipt{}, err
	}
	return receipt, nil
}

func (client *ReadinessClient) Acknowledge(ctx context.Context, transport ReadinessTransport, receipt ReadinessReceipt) error {
	if transport == nil || receipt.Validate() != nil {
		return ErrConfiguration
	}
	if ctx.Err() != nil {
		return ctx.Err()
	}
	attempt, err := NewReadinessAttempt()
	if err != nil {
		return err
	}
	identityBody, err := client.challengeBody()
	if err != nil {
		return err
	}
	var identity map[string]any
	if json.Unmarshal(identityBody, &identity) != nil {
		return ErrConfiguration
	}
	identity["receipt"] = receipt
	body, err := json.Marshal(identity)
	if err != nil {
		return ErrConfiguration
	}
	nonce, err := client.challenge(ctx, transport, "/friends/restricted-readiness/ack-challenge", body, attempt.ChallengeID)
	if err != nil {
		return err
	}
	proof, err := client.proof(nonce)
	if err != nil {
		return err
	}
	defer clear(proof)
	body, err = json.Marshal(struct {
		Receipt ReadinessReceipt `json:"receipt"`
		Proof   json.RawMessage  `json:"proof"`
	}{receipt, proof})
	if err != nil {
		return ErrConfiguration
	}
	defer clear(body)
	raw, err := transport.Post(ctx, "/friends/restricted-readiness/ack", body, attempt.FetchID)
	defer clear(raw)
	if ctx.Err() != nil {
		return ctx.Err()
	}
	if err != nil {
		return err
	}
	var response struct {
		Version     int    `json:"version"`
		Correlation string `json:"correlation_id"`
		Status      string `json:"status"`
	}
	if strictReadinessJSON(raw, 16384, &response) != nil || response.Version != 1 || response.Correlation != receipt.Correlation || response.Status != "ACK_RECEIVED" {
		return &ReadinessFailure{Code: "ACK_INCOMPATIBLE_RESPONSE"}
	}
	return nil
}
