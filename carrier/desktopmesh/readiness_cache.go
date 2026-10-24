package desktopmesh

import (
	"bytes"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

const MaxReadinessCache = 70000
const maxReadinessInteger = 9007199254740991

type ReadinessCode string

const (
	ReadinessReady       ReadinessCode = "READY"
	ReadinessMissing     ReadinessCode = "MISSING"
	ReadinessInvalid     ReadinessCode = "NATIVE_VALIDATION_FAILED"
	ReadinessBootstrap   ReadinessCode = "BOOTSTRAP_VALIDATION_FAILED"
	ReadinessExpired     ReadinessCode = "EXPIRED_ON_IMPORT"
	ReadinessDenied      ReadinessCode = "AUTHORIZATION_REJECTED"
	ReadinessStale       ReadinessCode = "STALE_STATE"
	ReadinessPersistence ReadinessCode = "PERSISTENCE_FAILED"
)

func (code ReadinessCode) Error() string { return string(code) }

type ReadinessAttempt struct {
	ChallengeID string `json:"challenge_id"`
	FetchID     string `json:"fetch_id"`
}

func (attempt ReadinessAttempt) Valid() bool {
	return validProbeID(attempt.ChallengeID) && validProbeID(attempt.FetchID) && attempt.ChallengeID != attempt.FetchID
}

func validProbeID(value string) bool {
	decoded, err := hex.DecodeString(value)
	return err == nil && len(decoded) == 16 && hex.EncodeToString(decoded) == value
}

type ReadinessStorage interface {
	Read() ([]byte, error)
	Write([]byte) error
}

type readinessState struct {
	Response    json.RawMessage   `json:"response"`
	Denied      bool              `json:"denied"`
	NextAttempt int64             `json:"next_attempt"`
	Context     *ReadinessAttempt `json:"receipt_context,omitempty"`
}

func (readinessState) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[readiness cache redacted]")
}

type ReadinessCache struct {
	mu       sync.Mutex
	storage  ReadinessStorage
	validate func([]byte, time.Time) ReadinessCode
	failed   bool
}

func (*ReadinessCache) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[readiness owner redacted]")
}

func NewReadinessCache(storage ReadinessStorage, public, anchor []byte) (*ReadinessCache, error) {
	if storage == nil || len(public) != 64 || len(anchor) != 32 {
		return nil, ErrConfiguration
	}
	public, anchor = bytes.Clone(public), bytes.Clone(anchor)
	return &ReadinessCache{storage: storage, validate: func(raw []byte, now time.Time) ReadinessCode {
		var delivery wholedevice.ReadinessDelivery
		if strictReadinessJSON(raw, wholedevice.MaxReadiness, &delivery) != nil {
			return ReadinessInvalid
		}
		if delivery.ExpiresAt <= now.Unix() {
			return ReadinessExpired
		}
		_, _, err := wholedevice.ValidateDelivery(raw, public, anchor, now)
		if errors.Is(err, wholedevice.ErrBootstrapValidation) {
			return ReadinessBootstrap
		}
		if err != nil {
			return ReadinessInvalid
		}
		return ReadinessReady
	}}, nil
}

func (cache *ReadinessCache) state() (readinessState, error) {
	if cache.failed {
		return readinessState{}, ReadinessPersistence
	}
	raw, err := cache.storage.Read()
	if err != nil {
		return readinessState{}, ReadinessPersistence
	}
	defer clear(raw)
	if raw == nil {
		return readinessState{Response: json.RawMessage("null")}, nil
	}
	var fields map[string]json.RawMessage
	if strictReadinessJSON(raw, MaxReadinessCache, &fields) != nil || fields == nil {
		return readinessState{}, ReadinessPersistence
	}
	for _, required := range []string{"response", "denied", "next_attempt"} {
		if fields[required] == nil || (required != "response" && bytes.Equal(fields[required], []byte("null"))) {
			return readinessState{}, ReadinessPersistence
		}
	}
	var state readinessState
	if strictReadinessJSON(raw, MaxReadinessCache, &state) != nil || state.NextAttempt < 0 || state.NextAttempt > maxReadinessInteger ||
		(state.Context != nil && !state.Context.Valid()) || (fields["receipt_context"] != nil && state.Context == nil) {
		return readinessState{}, ReadinessPersistence
	}
	return state, nil
}

func (cache *ReadinessCache) save(state readinessState) error {
	raw, err := json.Marshal(state)
	if err != nil || len(raw) > MaxReadinessCache {
		return ReadinessPersistence
	}
	defer clear(raw)
	if cache.storage.Write(raw) != nil {
		cache.failed = true
		return ReadinessPersistence
	}
	persisted, err := cache.storage.Read()
	defer clear(persisted)
	if err != nil || !bytes.Equal(raw, persisted) {
		cache.failed = true
		return ReadinessPersistence
	}
	return nil
}

func absent(raw json.RawMessage) bool {
	return len(raw) == 0 || bytes.Equal(bytes.TrimSpace(raw), []byte("null"))
}

func (cache *ReadinessCache) Usable(now time.Time) ([]byte, ReadinessCode) {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	state, err := cache.state()
	if err != nil {
		return nil, ReadinessPersistence
	}
	defer clear(state.Response)
	if state.Denied {
		return nil, ReadinessDenied
	}
	if absent(state.Response) {
		return nil, ReadinessMissing
	}
	code := cache.validate(state.Response, now)
	if code != ReadinessReady {
		return nil, code
	}
	return bytes.Clone(state.Response), ReadinessReady
}

func (cache *ReadinessCache) Attempt(now time.Time, required bool) (bool, error) {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	state, err := cache.state()
	if err != nil {
		return false, err
	}
	defer clear(state.Response)
	stamp := now.Unix()
	if stamp <= 0 || stamp > maxReadinessInteger-300 {
		return false, ErrConfiguration
	}
	if !required && state.NextAttempt > stamp {
		return false, nil
	}
	state.NextAttempt = stamp + 300
	if err := cache.save(state); err != nil {
		return false, err
	}
	return true, nil
}

func (cache *ReadinessCache) Deny() error {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	state, err := cache.state()
	if err != nil {
		return err
	}
	defer clear(state.Response)
	state.Denied = true
	return cache.save(state)
}

func (cache *ReadinessCache) Accept(raw []byte, attempt ReadinessAttempt, now time.Time) error {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	if !attempt.Valid() || len(raw) == 0 || len(raw) > wholedevice.MaxReadiness {
		return ErrConfiguration
	}
	if code := cache.validate(raw, now); code != ReadinessReady {
		return code
	}
	state, err := cache.state()
	if err != nil {
		return err
	}
	defer clear(state.Response)
	if !absent(state.Response) && readinessFloors(state.Response, raw, state.Denied) != nil {
		return ReadinessStale
	}
	state.Response = bytes.Clone(raw)
	defer clear(state.Response)
	state.Denied = false
	state.Context = &attempt
	return cache.save(state)
}

func readinessFloors(previous, incoming []byte, denied bool) error {
	var oldDelivery, nextDelivery wholedevice.ReadinessDelivery
	if strictReadinessJSON(previous, wholedevice.MaxReadiness, &oldDelivery) != nil || strictReadinessJSON(incoming, wholedevice.MaxReadiness, &nextDelivery) != nil {
		return ReadinessStale
	}
	if nextDelivery.IssuedAt < oldDelivery.IssuedAt || nextDelivery.Revision < oldDelivery.Revision || nextDelivery.MinimumCRL < oldDelivery.MinimumCRL ||
		(denied && (nextDelivery.IssuedAt <= oldDelivery.IssuedAt || nextDelivery.Challenge == oldDelivery.Challenge)) {
		return ReadinessStale
	}
	issuer := func(payload string) (map[string]any, int64, error) {
		raw, err := base64.StdEncoding.DecodeString(payload)
		defer clear(raw)
		var value map[string]any
		if err != nil || strictReadinessJSON(raw, 8192, &value) != nil {
			return nil, 0, ReadinessStale
		}
		number, valid := value["sequence"].(json.Number)
		sequence, err := number.Int64()
		if !valid || err != nil || sequence < 1 || sequence > maxReadinessInteger {
			return nil, 0, ReadinessStale
		}
		return value, sequence, nil
	}
	oldIssuer, oldSequence, oldError := issuer(oldDelivery.Issuer.Payload)
	nextIssuer, nextSequence, nextError := issuer(nextDelivery.Issuer.Payload)
	if oldError != nil || nextError != nil || nextSequence < oldSequence || (nextSequence == oldSequence && !reflect.DeepEqual(oldIssuer, nextIssuer)) {
		return ReadinessStale
	}
	directory := func(raw []byte) (map[string]any, time.Time, error) {
		var value map[string]any
		if strictReadinessJSON(raw, wholedevice.MaxReadiness, &value) != nil {
			return nil, time.Time{}, ReadinessStale
		}
		stamp, valid := value["issued_at"].(string)
		parsed, err := time.Parse(time.RFC3339Nano, stamp)
		if !valid || err != nil {
			return nil, time.Time{}, ReadinessStale
		}
		return value, parsed, nil
	}
	oldDirectory, oldTime, oldError := directory(oldDelivery.Directory)
	nextDirectory, nextTime, nextError := directory(nextDelivery.Directory)
	if oldError != nil || nextError != nil || nextTime.Before(oldTime) || (nextTime.Equal(oldTime) && !reflect.DeepEqual(oldDirectory, nextDirectory)) {
		return ReadinessStale
	}
	return nil
}
