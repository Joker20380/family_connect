package main

import "testing"

func TestPinnedChatServices(t *testing.T) {
	if pinnedChatServices(false) != nil {
		t.Fatal("implicit services")
	}
	services := pinnedChatServices(true)
	if len(services) != 2 || services["chat-api.family-connect.invalid"].String() != "185.251.89.19:8443" || services["chat-mailbox.family-connect.invalid"].String() != "127.0.0.1:4243" {
		t.Fatal("unbounded service map")
	}
}
