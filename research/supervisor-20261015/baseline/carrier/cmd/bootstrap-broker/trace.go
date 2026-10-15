package main

import (
	"sync"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func bufferedTrace(write func(sessiontrace.Event)) (func(sessiontrace.Event) bool, func()) {
	queue, done := make(chan sessiontrace.Event, 256), make(chan struct{})
	var state sync.RWMutex
	var once sync.Once
	closed := false
	go func() {
		defer close(done)
		for event := range queue {
			write(event)
		}
	}()
	sink := func(event sessiontrace.Event) bool {
		state.RLock()
		defer state.RUnlock()
		if closed {
			return false
		}
		select {
		case queue <- event:
			return true
		default:
			return false
		}
	}
	stop := func() {
		once.Do(func() {
			state.Lock()
			closed = true
			close(queue)
			state.Unlock()
		})
		<-done
	}
	return sink, stop
}
