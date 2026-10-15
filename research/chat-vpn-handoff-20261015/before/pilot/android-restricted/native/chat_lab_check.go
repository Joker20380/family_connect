//go:build android && fc_messenger_lab

package main

// #include <stdlib.h>
import "C"

import (
	"encoding/json"
	"io"
	"net"
	"os"
	"time"
	"unsafe"
)

//export fcMessengerSharing
func fcMessengerSharing(handle int64, response, identity, anchor, body string) *C.char {
	result := map[string]any{"scope": "JNI_OWNER_LOCAL_VPN_CONSUMER_NO_TUN", "pass": false}
	original := chatLease(handle)
	if original == nil || fcChatState(handle) != 1 {
		return C.CString(`{"error":"no_service_owner"}`)
	}
	chatMu.Lock()
	ownerMu.Lock()
	if current != nil || chatCurrent != original.chatSession {
		ownerMu.Unlock()
		chatMu.Unlock()
		return C.CString(`{"error":"busy"}`)
	}
	parent := &ownedSession{id: -1, ctx: original.ctx, session: original.session, profileHash: original.hash, state: 2, fd: -1}
	current = parent
	chatCurrent = nil
	ownerMu.Unlock()
	chatMu.Unlock()
	defer func() {
		chatMu.Lock()
		ownerMu.Lock()
		if current == parent {
			current = nil
		}
		if chatCurrent == nil {
			chatCurrent = original.chatSession
		}
		ownerMu.Unlock()
		chatMu.Unlock()
	}()
	borrowed := fcChatAcquire(response, identity, anchor, "1.1.1.1:53", 0)
	if borrowed != 0 {
		defer fcChatRelease(borrowed)
		deadline := time.Now().Add(2 * time.Second)
		for fcChatState(borrowed) == 0 && time.Now().Before(deadline) {
			time.Sleep(time.Millisecond)
		}
		result["borrowed_state"] = fcChatState(borrowed)
		descriptor := fcChatOpen(borrowed, 3000)
		if descriptor >= 0 {
			file := os.NewFile(uintptr(descriptor), "lab-cancel")
			connection, err := net.FileConn(file)
			file.Close()
			if err == nil {
				connection.SetReadDeadline(time.Now().Add(2 * time.Second))
				fcChatRelease(borrowed)
				buffer := make([]byte, 1024)
				for err == nil {
					_, err = connection.Read(buffer)
				}
				connection.Close()
				result["cancel_eof"] = err == io.EOF
			}
		}
		result["stale_state"] = fcChatState(borrowed)
		result["stale_open"] = fcChatOpen(borrowed, 100)
	}
	raw := fcChatRequest(handle, "/friends/chat/challenge", body, 5000)
	var request map[string]any
	json.Unmarshal([]byte(C.GoString(raw)), &request)
	C.free(unsafe.Pointer(raw))
	result["sibling_http_status"] = request["status"]
	result["original_state"] = fcChatState(handle)
	result["tun_created"] = parent.engine != nil || parent.fd >= 0
	result["pass"] = result["borrowed_state"] == int32(2) && result["cancel_eof"] == true && result["stale_state"] == int32(-1) && result["stale_open"] == int32(-1) && result["sibling_http_status"] == float64(200) && result["original_state"] == int32(1) && result["tun_created"] == false
	encoded, _ := json.Marshal(result)
	return C.CString(string(encoded))
}
