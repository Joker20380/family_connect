package main

/*
#include <stdint.h>
#include <string.h>
*/
import "C"

import (
	"context"
	"encoding/json"
	"sync"
	"time"
	"unsafe"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/iosbridge/bridge"
)

var registry = struct {
	sync.Mutex
	next  uint64
	items map[uint64]*bridge.Bridge
}{items: make(map[uint64]*bridge.Bridge)}

func lookup(handle C.uint64_t) *bridge.Bridge {
	registry.Lock()
	defer registry.Unlock()
	return registry.items[uint64(handle)]
}

//export fc_ios_start
func fc_ios_start(config unsafe.Pointer, size C.int32_t, mode C.int32_t) C.uint64_t {
	if size < 0 || size > 1<<20 || (size != 0 && config == nil) {
		return 0
	}
	registry.Lock()
	defer registry.Unlock()
	if len(registry.items) >= 4 {
		return 0
	}
	var open bridge.Opener
	switch mode {
	case 0:
		var material bridge.Material
		raw := C.GoBytes(config, C.int(size))
		err := json.Unmarshal(raw, &material)
		clear(raw)
		if err != nil {
			clear(material.Profile)
			clear(material.Directory)
			return 0
		}
		open = bridge.Live(material)
	case 1:
		open = bridge.NewFixture().Attach
	case 2:
		open = func(ctx context.Context) (*wholedevice.Session, error) { <-ctx.Done(); return nil, ctx.Err() }
	default:
		return 0
	}
	registry.next++
	registry.items[registry.next] = bridge.New(open)
	return C.uint64_t(registry.next)
}

//export fc_ios_state
func fc_ios_state(handle C.uint64_t) C.int32_t {
	owned := lookup(handle)
	if owned == nil {
		return bridge.Closed
	}
	state, failure := owned.Status()
	if failure != 0 {
		return C.int32_t(failure)
	}
	return C.int32_t(state)
}

//export fc_ios_write
func fc_ios_write(handle C.uint64_t, data unsafe.Pointer, size C.int32_t, family C.int32_t) C.int32_t {
	owned := lookup(handle)
	if owned == nil {
		return bridge.Closed
	}
	if data == nil || size <= 0 || size > bridge.MTU {
		return bridge.Invalid
	}
	return C.int32_t(owned.Write(unsafe.Slice((*byte)(data), int(size)), int(family)))
}

//export fc_ios_read
func fc_ios_read(handle C.uint64_t, output unsafe.Pointer, capacity C.int32_t, family *C.int32_t, wait C.int32_t) C.int32_t {
	owned := lookup(handle)
	if owned == nil {
		return bridge.Closed
	}
	if output == nil || family == nil || capacity < bridge.MTU {
		return bridge.Invalid
	}
	data, protocol, code := owned.Read(time.Duration(wait) * time.Millisecond)
	if code != 0 {
		return C.int32_t(code)
	}
	copy(unsafe.Slice((*byte)(output), int(capacity)), data)
	*family = C.int32_t(protocol)
	return C.int32_t(len(data))
}

//export fc_ios_cancel
func fc_ios_cancel(handle C.uint64_t) {
	if owned := lookup(handle); owned != nil {
		owned.Cancel()
	}
}

//export fc_ios_stop
func fc_ios_stop(handle C.uint64_t) {
	if owned := lookup(handle); owned != nil {
		owned.Stop()
	}
	registry.Lock()
	delete(registry.items, uint64(handle))
	registry.Unlock()
}

//export fc_ios_handles
func fc_ios_handles() C.int32_t {
	registry.Lock()
	defer registry.Unlock()
	return C.int32_t(len(registry.items))
}

func main() {}
