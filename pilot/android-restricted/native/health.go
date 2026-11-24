//go:build android

package main

// #include <stdlib.h>
import "C"

import (
	"encoding/base64"
	"time"
)

//export fcRestrictedDns
func fcRestrictedDns(id int64, encoded string, millis int32) *C.char {
	query, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil || len(query) < 17 || len(query) > 512 || millis < 1 || millis > 2500 {
		return nil
	}
	if !ownerMu.TryLock() {
		return nil
	}
	owned := current
	if owned == nil || owned.id != id {
		ownerMu.Unlock()
		return nil
	}
	if !owned.mu.TryLock() {
		ownerMu.Unlock()
		return nil
	}
	if owned.state != 2 || owned.session == nil || owned.session.Failed() {
		owned.mu.Unlock()
		ownerMu.Unlock()
		return nil
	}
	session := owned.session
	owned.mu.Unlock()
	ownerMu.Unlock()
	response := make(chan []byte, 1)
	session.HandleDNSDatagram(query, "10.79.0.1", 53, func(answer []byte) error {
		select {
		case response <- append([]byte(nil), answer...):
		default:
		}
		return nil
	})
	timer := time.NewTimer(time.Duration(millis) * time.Millisecond)
	defer timer.Stop()
	select {
	case answer := <-response:
		if owned.ctx.Err() != nil {
			return nil
		}
		return C.CString(base64.StdEncoding.EncodeToString(answer))
	case <-timer.C:
		return nil
	case <-owned.ctx.Done():
		return nil
	}
}
