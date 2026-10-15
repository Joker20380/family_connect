package roombroker

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestTelemostProvider(t *testing.T) {
	for _, test := range []struct {
		name   string
		status int
		body   string
		code   Code
	}{
		{"success", 201, `{"id":"fresh","join_url":"https://telemost.yandex.ru/j/new-room","extra":true}`, ""},
		{"bad_request", 400, "fake-secret", "provider_bad_request"},
		{"unauthorized", 401, "fake-secret", "provider_unauthorized"},
		{"forbidden", 403, "fake-secret", "provider_forbidden"},
		{"limited", 429, "fake-secret", "provider_rate_limited"},
		{"unavailable", 503, "fake-secret", "provider_unavailable"},
		{"unexpected", 200, "fake-secret", "provider_status"},
		{"json", 201, `{`, "provider_json"},
		{"duplicate", 201, `{"id":"a","id":"b"}`, "provider_json"},
		{"trailing", 201, `{} {}`, "provider_json"},
		{"missing_id", 201, `{"join_url":"https://telemost.yandex.ru/j/new-room"}`, "provider_id"},
		{"empty_id", 201, `{"id":""}`, "provider_id"},
		{"missing_url", 201, `{"id":"fresh"}`, "provider_join_url"},
		{"bad_url", 201, `{"id":"fresh","join_url":"https://evil.test/j/new"}`, "provider_join_url"},
		{"oversized", 201, strings.Repeat("x", maxResponse+1), "provider_body"},
	} {
		t.Run(test.name, func(t *testing.T) {
			calls := 0
			server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
				calls++
				raw, _ := io.ReadAll(request.Body)
				if request.Method != "POST" || request.URL.Path != "/v1/telemost-api/conferences" ||
					request.Header.Get("Authorization") != "OAuth fake-secret" || request.Header.Get("Content-Type") != "application/json" ||
					string(raw) != `{"waiting_room_level":"PUBLIC"}` {
					t.Error("incorrect provider request")
				}
				writer.WriteHeader(test.status)
				_, _ = io.WriteString(writer, test.body)
			}))
			defer server.Close()
			provider := &TelemostRoomProvider{"fake-secret", server.Client(), server.URL + "/v1/telemost-api/conferences"}
			room, err := provider.CreateRoom(context.Background())
			if test.code == "" {
				if err != nil || room.ID != "fresh" || !ValidJoinURL(room.JoinURL) {
					t.Fatal("success parsing failed", err)
				}
			} else if err != test.code {
				t.Fatalf("expected %s, got %v", test.code, err)
			}
			if calls != 1 || strings.Contains(fmt.Sprint(err), "fake-secret") {
				t.Fatal("retry or secret leak")
			}
		})
	}
}

func TestProviderCancellationTimeoutAndRedirect(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		_, _ = io.Copy(io.Discard, request.Body)
		select {
		case <-request.Context().Done():
		case <-time.After(time.Second):
		}
	}))
	defer server.Close()
	provider := &TelemostRoomProvider{"fake-secret", server.Client(), server.URL}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := provider.CreateRoom(ctx); err != Code("provider_cancelled") {
		t.Fatal(err)
	}
	ctx, cancel = context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if _, err := provider.CreateRoom(ctx); err != Code("provider_timeout") {
		t.Fatal(err)
	}
	t.Setenv("YANDEX_TELEMOST_OAUTH_TOKEN", "fake-secret")
	provider, err := NewTelemostRoomProvider()
	if err != nil {
		t.Fatal(err)
	}
	redirect := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		http.Redirect(writer, request, "http://127.0.0.1:1/credential-leak", 302)
	}))
	defer redirect.Close()
	provider.endpoint = redirect.URL
	if _, err := provider.CreateRoom(context.Background()); err != Code("provider_status") {
		t.Fatal(err)
	}
	t.Setenv("YANDEX_TELEMOST_OAUTH_TOKEN", "")
	if _, err := NewTelemostRoomProvider(); err == nil {
		t.Fatal("missing token accepted")
	}
}

func TestJoinURLAndRedaction(t *testing.T) {
	for _, value := range []string{"", "http://telemost.yandex.ru/j/a", "https://telemost.yandex.ru:443/j/a", "https://user@telemost.yandex.ru/j/a", "https://telemost.yandex.ru/j/a?", "https://telemost.yandex.ru/j/a#secret", "https://telemost.yandex.ru/j/%61", "https://telemost.yandex.ru/j/a/b"} {
		if ValidJoinURL(value) {
			t.Fatal("bad URL accepted")
		}
	}
	room := Room{"private-id", "https://telemost.yandex.ru/j/secret"}
	descriptor := Descriptor{JoinURL: room.JoinURL}
	if strings.Contains(fmt.Sprintf("%v %+v %#v %v %#v", room, room, room, descriptor, descriptor), "secret") {
		t.Fatal("format leaked room")
	}
}
