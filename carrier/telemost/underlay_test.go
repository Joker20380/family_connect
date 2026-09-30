package telemost

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/underlay"
)

func TestRestrictedHTTPAndWebSocketCannotBypassProtection(test *testing.T) {
	server := httptest.NewServer(http.NotFoundHandler())
	defer server.Close()
	network, err := underlay.New(context.Background(), "127.0.0.1:53", func(int) bool { return false })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	session, err := New(context.Background(), Config{RoomURL: "test-room", Underlay: network, HTTPClient: server.Client()})
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	if response, err := session.auth.Client.Get(server.URL); err == nil {
		response.Body.Close()
		test.Fatal("custom HTTP client bypassed protected network")
	}
	session.wsURL = "ws" + strings.TrimPrefix(server.URL, "http")
	if err := session.dialWebSocket(context.Background()); err == nil {
		test.Fatal("WebSocket bypassed protected network")
	}
	if network.Rejected.Load() != 2 || network.Protected.Load() != 0 {
		test.Fatal("signaling protection paths not enforced")
	}
}
