package startupdiag

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"os"
	"sync"
	"testing"
)

func TestCorrelationAttemptIsolationAndBound(test *testing.T) {
	vpn := Start(context.Background(), 1)
	chat := Start(vpn, 2)
	nonce := [32]byte{1}
	first := Bootstrap(vpn, hex.EncodeToString(nonce[:]))
	BootstrapAuthenticated(first)
	var workers sync.WaitGroup
	for index := 2; index < 10; index++ {
		workers.Add(1)
		go func(index int) {
			defer workers.Done()
			nonce := [32]byte{byte(index)}
			ctx := Bootstrap(vpn, hex.EncodeToString(nonce[:]))
			BootstrapAuthenticated(ctx)
			Snapshot(vpn)
		}(index)
	}
	workers.Wait()
	snapshot := Snapshot(vpn)
	if len(snapshot.BootstrapExchanges) != 4 || snapshot.BootstrapExchangesDropped != 5 || len(Snapshot(chat).BootstrapExchanges) != 0 {
		test.Fatal("attempt bound/isolation")
	}
	firstTag := snapshot.BootstrapExchanges[0].Tag
	snapshot.BootstrapExchanges[0].Tag = "mutated"
	Failure(first, "HELLO_RECEIVE", os.ErrDeadlineExceeded)
	Stop(first, "CLEANUP")
	Cancel(first)
	Complete(first, context.Canceled)
	actual := Snapshot(vpn)
	if actual.Observation.BootstrapExchangeTag != firstTag || actual.Cause != "IO_DEADLINE" || actual.BootstrapExchanges[0].Tag != firstTag {
		test.Fatal("first failure/clone lost")
	}
	before, _ := json.Marshal(actual)
	BootstrapAuthenticated(Bootstrap(vpn, hex.EncodeToString(nonce[:])))
	after, _ := json.Marshal(Snapshot(vpn))
	if string(before) != string(after) {
		test.Fatal("late exchange changed closed attempt")
	}
	inherited := Start(first, 3)
	BootstrapAuthenticated(inherited)
	if len(Snapshot(inherited).BootstrapExchanges) != 0 {
		test.Fatal("inherited handle altered new attempt")
	}
}
