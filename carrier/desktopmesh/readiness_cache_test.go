package desktopmesh

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type memoryReadiness struct {
	raw       []byte
	failRead  bool
	failWrite bool
	torn      bool
	writes    int
}

func (storage *memoryReadiness) Read() ([]byte, error) {
	if storage.failRead {
		return nil, errors.New("synthetic storage failure")
	}
	return bytes.Clone(storage.raw), nil
}

func (storage *memoryReadiness) Write(raw []byte) error {
	storage.writes++
	if storage.failWrite {
		return errors.New("synthetic write failure")
	}
	storage.raw = bytes.Clone(raw)
	if storage.torn {
		storage.raw = []byte("{}")
	}
	return nil
}

func policyMaterial(test *testing.T) []byte {
	test.Helper()
	issuer := base64.StdEncoding.EncodeToString([]byte(`{"version":1,"sequence":2,"family":"synthetic"}`))
	return []byte(fmt.Sprintf(`{"version":1,"device":"synthetic","challenge":"%s","issued_at":100,"expires_at":1000,"revision":3,"minimum_crl":4,"issuer":{"payload":"%s","signature":"synthetic"},"certificate":"synthetic","revocations":"synthetic","directory":{"issued_at":"2026-10-22T12:00:00Z","expires_at":"2026-10-22T13:00:00Z","seeds":[]}}`, base64.StdEncoding.EncodeToString(make([]byte, 32)), issuer))
}

func policyCache(test *testing.T, storage *memoryReadiness) *ReadinessCache {
	test.Helper()
	cache, err := NewReadinessCache(storage, make([]byte, 64), make([]byte, 32))
	if err != nil {
		test.Fatal(err)
	}
	cache.validate = func(raw []byte, now time.Time) ReadinessCode {
		var delivery wholedevice.ReadinessDelivery
		if strictReadinessJSON(raw, wholedevice.MaxReadiness, &delivery) != nil {
			return ReadinessInvalid
		}
		if delivery.ExpiresAt <= now.Unix() {
			return ReadinessExpired
		}
		return ReadinessReady
	}
	return cache
}

func cacheAttempt() ReadinessAttempt {
	return ReadinessAttempt{strings.Repeat("a", 32), strings.Repeat("b", 32)}
}

func TestReadinessCacheValidationCannotBeBypassedByPolicyFixture(test *testing.T) {
	cache, err := NewReadinessCache(&memoryReadiness{}, make([]byte, 64), make([]byte, 32))
	if err != nil {
		test.Fatal(err)
	}
	if err := cache.Accept(policyMaterial(test), cacheAttempt(), time.Unix(200, 0)); err != ReadinessInvalid {
		test.Fatalf("untrusted policy fixture accepted: %v", err)
	}
}

func TestReadinessCacheImportRestartExpiryAndDenial(test *testing.T) {
	storage := &memoryReadiness{}
	cache := policyCache(test, storage)
	now := time.Unix(200, 0)
	if raw, code := cache.Usable(now); raw != nil || code != ReadinessMissing {
		test.Fatal(code)
	}
	material := policyMaterial(test)
	if err := cache.Accept(material, cacheAttempt(), now); err != nil {
		test.Fatal(err)
	}
	before := bytes.Clone(storage.raw)
	cache = policyCache(test, storage)
	raw, code := cache.Usable(now)
	if code != ReadinessReady || !bytes.Equal(raw, material) {
		test.Fatal("restart cache unavailable")
	}
	clear(raw)
	if !bytes.Equal(before, storage.raw) {
		test.Fatal("caller mutated durable cache")
	}
	if raw, code := cache.Usable(time.Unix(1000, 0)); raw != nil || code != ReadinessExpired {
		test.Fatal("expired response usable")
	}
	if err := cache.Deny(); err != nil {
		test.Fatal(err)
	}
	if raw, code := cache.Usable(now); raw != nil || code != ReadinessDenied {
		test.Fatal("denied response usable")
	}
	if err := cache.Accept(material, cacheAttempt(), now); err != ReadinessStale {
		test.Fatal("same denied challenge reaccepted")
	}
	fresh := bytes.Replace(material, []byte(`"issued_at":100`), []byte(`"issued_at":101`), 1)
	fresh = bytes.Replace(fresh, []byte(base64.StdEncoding.EncodeToString(make([]byte, 32))), []byte(base64.StdEncoding.EncodeToString(bytes.Repeat([]byte{1}, 32))), 1)
	if err := cache.Accept(fresh, cacheAttempt(), now); err != nil {
		test.Fatal("fresh authorization rejected", err)
	}
}

func TestReadinessCacheFloorsAndEquivocation(test *testing.T) {
	changes := []struct{ old, next string }{
		{`"issued_at":100`, `"issued_at":99`}, {`"revision":3`, `"revision":2`}, {`"minimum_crl":4`, `"minimum_crl":3`},
		{"2026-10-22T12:00:00Z", "2026-10-22T11:59:59Z"}, {`"seeds":[]`, `"seeds":["different"]`},
		{base64.StdEncoding.EncodeToString([]byte(`{"version":1,"sequence":2,"family":"synthetic"}`)), base64.StdEncoding.EncodeToString([]byte(`{"version":1,"sequence":1,"family":"synthetic"}`))},
		{base64.StdEncoding.EncodeToString([]byte(`{"version":1,"sequence":2,"family":"synthetic"}`)), base64.StdEncoding.EncodeToString([]byte(`{"version":1,"sequence":2,"family":"other"}`))},
	}
	for _, change := range changes {
		storage := &memoryReadiness{}
		cache := policyCache(test, storage)
		material := policyMaterial(test)
		if err := cache.Accept(material, cacheAttempt(), time.Unix(200, 0)); err != nil {
			test.Fatal(err)
		}
		before := bytes.Clone(storage.raw)
		next := bytes.Replace(material, []byte(change.old), []byte(change.next), 1)
		if bytes.Equal(material, next) {
			test.Fatal("mutation not applied")
		}
		if err := cache.Accept(next, cacheAttempt(), time.Unix(200, 0)); err != ReadinessStale || !bytes.Equal(before, storage.raw) {
			test.Fatalf("floor accepted or old state lost: %v", err)
		}
	}
}

func TestReadinessCacheCorruptionAndUncertainWriteFailClosed(test *testing.T) {
	for _, raw := range []string{`{}`, `{"response":null,"denied":false,"denied":false,"next_attempt":0}`,
		`{"response":null,"denied":null,"next_attempt":0}`, `{"response":null,"denied":false,"next_attempt":-1}`,
		`{"response":null,"denied":false,"next_attempt":0,"extra":1}`, `{"response":null,"denied":false,"next_attempt":0,"receipt_context":null}`,
		strings.Repeat(" ", MaxReadinessCache+1)} {
		cache := policyCache(test, &memoryReadiness{raw: []byte(raw)})
		if _, code := cache.Usable(time.Unix(200, 0)); code != ReadinessPersistence {
			test.Fatal("corruption accepted", code)
		}
	}
	for _, torn := range []bool{false, true} {
		storage := &memoryReadiness{}
		cache := policyCache(test, storage)
		if err := cache.Accept(policyMaterial(test), cacheAttempt(), time.Unix(200, 0)); err != nil {
			test.Fatal(err)
		}
		storage.failWrite, storage.torn = !torn, torn
		if err := cache.Deny(); err != ReadinessPersistence {
			test.Fatal("uncertain denial ignored")
		}
		storage.failWrite, storage.torn = false, false
		if raw, code := cache.Usable(time.Unix(200, 0)); raw != nil || code != ReadinessPersistence {
			test.Fatal("uncertain write reused old authorization")
		}
	}
}

func TestReadinessAttemptCooldownAndConcurrentOwner(test *testing.T) {
	storage := &memoryReadiness{}
	cache := policyCache(test, storage)
	var workers sync.WaitGroup
	var successes int
	var lock sync.Mutex
	for index := 0; index < 12; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			attempt, err := cache.Attempt(time.Unix(200, 0), false)
			if err != nil {
				test.Error(err)
			}
			if attempt {
				lock.Lock()
				successes++
				lock.Unlock()
			}
		}()
	}
	workers.Wait()
	if successes != 1 || storage.writes != 1 {
		test.Fatal("multiple refresh attempts")
	}
	if attempt, err := cache.Attempt(time.Unix(201, 0), true); !attempt || err != nil {
		test.Fatal("required reconnect blocked by cooldown")
	}
	if attempt, err := cache.Attempt(time.Unix(501, 0), false); !attempt || err != nil {
		test.Fatal("refresh did not resume after cooldown")
	}
	var fields map[string]any
	if json.Unmarshal(storage.raw, &fields) != nil || fields["next_attempt"] != float64(801) {
		test.Fatal("cooldown not persisted")
	}
}
