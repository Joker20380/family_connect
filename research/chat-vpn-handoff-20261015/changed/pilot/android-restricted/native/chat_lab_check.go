//go:build android && fc_messenger_lab

package main

// #include <stdlib.h>
// #include <stdint.h>
// int fcRestrictedProtect(uintptr_t owner, int fd);
// void fcRestrictedRelease(uintptr_t owner);
import "C"

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"io"
	"net"
	"os"
	"time"
	"unsafe"
)

//export fcMessengerSharing
func fcMessengerSharing(handle int64, response, identity, anchor, body string, protector C.uintptr_t) *C.char {
	defer C.fcRestrictedRelease(protector)
	result := map[string]any{"scope": "JNI_OWNER_LOCAL_VPN_CONSUMER_NO_TUN", "pass": false}
	original := chatLease(handle)
	if original == nil || fcChatState(handle) != 1 {
		return C.CString(`{"error":"no_service_owner"}`)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	vpn, err := transportOwner.ReserveVPN(ctx)
	if err != nil {
		return C.CString(`{"error":"busy"}`)
	}
	defer vpn.Release()
	if vpn.Wait(ctx) != nil {
		return C.CString(`{"error":"cleanup"}`)
	}
	material := []byte(identity)
	defer clear(material)
	profile, seed, err := wholedevice.DeliveryMaterial([]byte(response), material, []byte(anchor), time.Now())
	if err != nil {
		return C.CString(`{"error":"material"}`)
	}
	defer clear(profile)
	network, err := underlay.New(ctx, "1.1.1.1:53", func(fd int) bool { return C.fcRestrictedProtect(protector, C.int(fd)) != 0 })
	if err != nil {
		return C.CString(`{"error":"underlay"}`)
	}
	defer network.Close()
	session, err := openChatSession(ctx, profile, seed, network, func(string) {})
	if err != nil {
		return C.CString(`{"error":"open"}`)
	}
	defer session.Close()
	if vpn.Publish(session, sha256.Sum256(profile)) != nil {
		return C.CString(`{"error":"publish"}`)
	}
	sibling := fcChatAcquire(response, identity, anchor, "1.1.1.1:53", 0)
	defer fcChatRelease(sibling)
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
	raw := fcChatRequest(sibling, "/friends/chat/challenge", body, 5000)
	var request map[string]any
	json.Unmarshal([]byte(C.GoString(raw)), &request)
	C.free(unsafe.Pointer(raw))
	result["sibling_http_status"] = request["status"]
	result["original_state"] = fcChatState(handle)
	result["tun_created"] = false
	result["pass"] = result["borrowed_state"] == int32(2) && result["cancel_eof"] == true && result["stale_state"] == int32(-1) && result["stale_open"] == int32(-1) && result["sibling_http_status"] == float64(200) && result["original_state"] == int32(-1)
	encoded, _ := json.Marshal(result)
	return C.CString(string(encoded))
}
