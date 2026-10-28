package main

import "testing"

func TestPinnedChatServices(t *testing.T) {
	services, err := pinnedChatServices(false, "")
	if err != nil || services != nil {
		t.Fatal("implicit services")
	}
	services, err = pinnedChatServices(true, "192.0.2.12:8443")
	if err != nil || len(services) != 2 || services["chat-api.family-connect.invalid"].String() != "192.0.2.12:8443" || services["chat-mailbox.family-connect.invalid"].String() != "127.0.0.1:4243" {
		t.Fatal("fixed service map changed")
	}
	for _, target := range []string{"", "example.invalid:8443", "192.0.2.12:0", "127.0.0.1:8443", "10.0.0.1:8443", "0.0.0.0:8443", "[::1]:8443", "192.0.2.12:8443\n"} {
		if _, err := pinnedChatServices(true, target); err == nil {
			t.Fatal("invalid target accepted")
		}
	}
	if _, err := pinnedChatServices(false, "192.0.2.12:8443"); err == nil {
		t.Fatal("disabled target accepted")
	}
}
