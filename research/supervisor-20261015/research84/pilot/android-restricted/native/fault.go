//go:build android

package main

import "C"

import (
	"encoding/json"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"strings"
)

//export fcRestrictedFault
func fcRestrictedFault(command string) *C.char {
	ownerMu.Lock()
	defer ownerMu.Unlock()
	var trace *sessiontrace.Recorder
	if current != nil {
		trace = sessiontrace.From(current.ctx)
	}
	if strings.HasPrefix(command, "correlation:") {
		return C.CString(trace.CorrelationCommand(strings.TrimPrefix(command, "correlation:"), "client"))
	}
	raw, _ := json.Marshal(trace.FaultCommand(command))
	return C.CString(string(raw))
}
