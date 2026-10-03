package main

import (
	"sync"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestTraceLateCallbacksAndBound(test *testing.T) {
	entered, release := make(chan struct{}), make(chan struct{})
	var first sync.Once
	sink, stop := bufferedTrace(func(sessiontrace.Event) {
		first.Do(func() { close(entered) })
		<-release
	})
	if !sink(sessiontrace.Event{}) {
		test.Fatal("initial event rejected")
	}
	<-entered
	for index := 0; index < 256; index++ {
		if !sink(sessiontrace.Event{}) {
			test.Fatal("unexpected queue bound")
		}
	}
	if sink(sessiontrace.Event{}) {
		test.Fatal("unbounded trace queue")
	}
	close(release)
	var workers sync.WaitGroup
	for index := 0; index < 8; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for count := 0; count < 100; count++ {
				sink(sessiontrace.Event{})
			}
		}()
	}
	stop()
	workers.Wait()
	stop()
	if sink(sessiontrace.Event{}) {
		test.Fatal("late callback accepted after shutdown")
	}
}
