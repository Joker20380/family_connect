package familysession

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"testing"
	"time"
)

func TestExpiredRecoveryStrictFamilyTLS(test *testing.T) {
	path := os.Getenv("FC_EXPIRED_RECOVERY_FIXTURE")
	if path == "" {
		test.Skip("explicit disposable expired recovery fixture required")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		test.Fatal("fixture unavailable")
	}
	var fixture struct {
		ServerBefore Credentials   `json:"server_before"`
		ServerAfter  Credentials   `json:"server_after"`
		ClientsAfter []Credentials `json:"clients_after"`
	}
	if json.Unmarshal(raw, &fixture) != nil || len(fixture.ClientsAfter) != 3 {
		test.Fatal("fixture schema invalid")
	}
	if _, _, err := Configuration(encoded(fixture.ServerBefore), true); !errors.Is(err, ErrRejected) {
		test.Fatal("expired predecessor accepted by normal validator")
	}
	if _, _, err := Configuration(encoded(fixture.ServerAfter), true); err != nil {
		test.Fatal("successor rejected by normal validator")
	}
	for _, client := range fixture.ClientsAfter {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		connect(test, ctx, client, fixture.ServerAfter)
		cancel()
	}
}
