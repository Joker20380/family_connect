package localwrite

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestCompletionAndCancellation(test *testing.T) {
	for _, mode := range []string{"complete", "obsolete_queued", "obsolete_partial", "deadline_queued", "deadline_partial", "error", "late", "legacy"} {
		test.Run(mode, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			obsolete := make(chan struct{})
			observed, completion := Observe(ctx, obsolete)
			if mode == "legacy" {
				if completion.Wait() != nil {
					test.Fatal("legacy")
				}
				return
			}
			registered, err := Register(observed, 2)
			if err != nil {
				test.Fatal(err)
			}
			if _, err = Register(observed, 2); err == nil {
				test.Fatal("reused completion")
			}
			if mode == "obsolete_queued" {
				close(obsolete)
				if completion.Wait() != nil || registered.Begin() {
					test.Fatal("obsolete wrote")
				}
				return
			}
			if mode == "deadline_queued" {
				cancel()
				if !errors.Is(completion.Wait(), context.Canceled) || registered.Begin() {
					test.Fatal("cancelled wrote")
				}
				return
			}
			if !registered.Begin() {
				test.Fatal("not writing")
			}
			registered.Complete(nil)
			done := make(chan error, 1)
			go func() { done <- completion.Wait() }()
			select {
			case <-done:
				test.Fatal("completed partial message")
			case <-time.After(time.Millisecond):
			}
			if mode == "obsolete_partial" {
				close(obsolete)
				if !registered.Begin() {
					test.Fatal("partial aborted")
				}
			}
			if mode == "deadline_partial" || mode == "late" {
				cancel()
				if !errors.Is(<-done, context.Canceled) {
					test.Fatal("deadline ignored")
				}
				freshCtx, fresh := Observe(context.Background(), nil)
				next, _ := Register(freshCtx, 1)
				registered.Complete(nil)
				next.Begin()
				next.Complete(nil)
				if fresh.Wait() != nil {
					test.Fatal("late completion changed fresh generation")
				}
				return
			}
			failure := errors.New("write failed")
			if mode == "error" {
				registered.Complete(failure)
				if !errors.Is(<-done, failure) {
					test.Fatal("error lost")
				}
				return
			}
			registered.Complete(nil)
			if <-done != nil {
				test.Fatal("completion failed")
			}
		})
	}
}
