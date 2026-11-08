package main

// #include <stdlib.h>
import "C"

import (
	"encoding/base64"
	"time"
)

//export fcAwgDns
func fcAwgDns(id int32, source, encoded string, millis int32) *C.char {
	query, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil || len(query) < 17 || len(query) > 512 || millis < 1 || millis > 2500 {
		return nil
	}
	if !handlesMu.TryRLock() {
		return nil
	}
	handle, exists := tunnelHandles[id]
	handlesMu.RUnlock()
	if !exists || handle.health == nil {
		return nil
	}
	answer := handle.health.query(source, query, time.Duration(millis)*time.Millisecond)
	if len(answer) == 0 {
		return nil
	}
	return C.CString(base64.StdEncoding.EncodeToString(answer))
}
