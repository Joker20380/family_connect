//go:build seedacceptance && linux

package telemost

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

func TestAcceptanceRealGorillaBoundary(test *testing.T) {
	closed := make(chan struct{})
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		upgrader := websocket.Upgrader{}
		connection, err := upgrader.Upgrade(writer, request, nil)
		if err != nil {
			return
		}
		defer close(closed)
		defer connection.Close()
		for {
			kind, payload, err := connection.ReadMessage()
			if err != nil {
				return
			}
			if connection.WriteMessage(kind, payload) != nil {
				return
			}
		}
	}))
	defer server.Close()
	upstream, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		test.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	bridge, err := newAcceptanceBridge(ctx, upstream)
	if err != nil {
		test.Fatal(err)
	}
	defer bridge.client.Close()
	for range 5 {
		if bridge.client.WriteJSON(map[string]string{"nonce": "synthetic-local"}) != nil {
			test.Fatal("send")
		}
		var message map[string]string
		if bridge.client.ReadJSON(&message) != nil || message["nonce"] != "synthetic-local" {
			test.Fatal("transparent forwarding")
		}
	}
	result := make(chan error, 1)
	go func() { var message map[string]any; result <- bridge.client.ReadJSON(&message) }()
	if !bridge.end(1011, true) {
		test.Fatal("not applied")
	}
	select {
	case <-closed:
	case <-time.After(time.Second):
		test.Fatal("real upstream still open")
	}
	select {
	case err := <-result:
		var closeError *websocket.CloseError
		if !errors.As(err, &closeError) || closeError.Code != 1011 || closeError.Text != "" {
			test.Fatalf("not real Gorilla CloseError: %T", err)
		}
		classification := classifySignalingRead(err, ctx, false)
		if classification.Kind != "WS_CLOSE" || classification.CloseCode != 1011 || classification.ContextState != "ACTIVE" || classification.CarrierClosed {
			test.Fatal(classification)
		}
		test.Logf("REAL_UPSTREAM_CLOSED=true REAL_CLOSE_FRAME=true error_type=%T code=1011 context=ACTIVE provider_generated=false", err)
	case <-time.After(time.Second):
		test.Fatal("reader did not see close frame")
	}
	if bridge.end(1011, true) {
		test.Fatal("replay")
	}
	select {
	case <-bridge.done:
	case <-time.After(time.Second):
		test.Fatal("pump leak")
	}
}

func TestAcceptanceDisabledBoundary(test *testing.T) {
	session := testSession(test)
	connection := &websocket.Conn{}
	actual, err := session.researchSignalingBoundary(connection)
	if err != nil || actual != connection || session.bridge.Load() != nil {
		test.Fatal("disabled changed transport")
	}
	if session.ResearchCloseSeed1011() {
		test.Fatal("disabled allowed trigger")
	}
}

func TestAcceptanceNaturalCloseFailClosed(test *testing.T) {
	for _, code := range []int{1000, 1002, 1007, 1008, 1011} {
		test.Run(strconv.Itoa(code), func(test *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
				upgrader := websocket.Upgrader{}
				connection, err := upgrader.Upgrade(writer, request, nil)
				if err != nil {
					return
				}
				defer connection.Close()
				var message any
				connection.ReadJSON(&message)
				connection.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(code, "PRIVATE_REASON"), time.Now().Add(time.Second))
			}))
			defer server.Close()
			upstream, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
			if err != nil {
				test.Fatal(err)
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			bridge, err := newAcceptanceBridge(ctx, upstream)
			if err != nil {
				test.Fatal(err)
			}
			defer bridge.client.Close()
			bridge.client.WriteJSON(map[string]string{"nonce": "local"})
			var message any
			err = bridge.client.ReadJSON(&message)
			var closeError *websocket.CloseError
			if !errors.As(err, &closeError) || closeError.Code != code || closeError.Text != "" || bridge.triggered.Load() {
				test.Fatalf("boundary %T", err)
			}
			select {
			case <-bridge.done:
			case <-time.After(time.Second):
				test.Fatal("pump leak")
			}
		})
	}
}
