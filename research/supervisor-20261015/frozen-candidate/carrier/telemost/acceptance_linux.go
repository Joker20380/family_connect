//go:build seedacceptance && linux

package telemost

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"net"
	"net/http"
	"net/url"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

type acceptanceKey struct{}

func WithResearchSeedBoundary(ctx context.Context, roomHash string) context.Context {
	return context.WithValue(ctx, acceptanceKey{}, roomHash)
}

type acceptanceBoundary struct {
	bridge atomic.Pointer[acceptanceBridge]
}

type acceptanceBridge struct {
	upstream  *websocket.Conn
	server    *websocket.Conn
	client    *websocket.Conn
	ending    sync.Once
	workers   sync.WaitGroup
	triggered atomic.Bool
	done      chan struct{}
}

type pipeUpgrade struct {
	connection net.Conn
	reader     *bufio.Reader
	header     http.Header
}

func (upgrade *pipeUpgrade) Header() http.Header { return upgrade.header }
func (upgrade *pipeUpgrade) WriteHeader(int)     {}
func (upgrade *pipeUpgrade) Write([]byte) (int, error) {
	return 0, errors.New("research_upgrade_failed")
}
func (upgrade *pipeUpgrade) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	return upgrade.connection, bufio.NewReadWriter(upgrade.reader, bufio.NewWriter(upgrade.connection)), nil
}

func newAcceptanceBridge(ctx context.Context, upstream *websocket.Conn) (*acceptanceBridge, error) {
	clientPipe, serverPipe := net.Pipe()
	deadline := time.Now().Add(time.Second)
	clientPipe.SetDeadline(deadline)
	serverPipe.SetDeadline(deadline)
	serverResult := make(chan *websocket.Conn, 1)
	go func() {
		reader := bufio.NewReader(serverPipe)
		request, err := http.ReadRequest(reader)
		if err != nil {
			serverPipe.Close()
			serverResult <- nil
			return
		}
		upgrader := websocket.Upgrader{CheckOrigin: func(*http.Request) bool { return true }}
		server, err := upgrader.Upgrade(&pipeUpgrade{serverPipe, reader, make(http.Header)}, request, nil)
		if err != nil {
			serverPipe.Close()
			serverResult <- nil
			return
		}
		serverResult <- server
	}()
	client, _, err := websocket.NewClient(clientPipe, &url.URL{Scheme: "ws", Host: "research.invalid", Path: "/"}, nil, 4096, 4096)
	server := <-serverResult
	if err != nil || server == nil {
		clientPipe.Close()
		serverPipe.Close()
		upstream.Close()
		return nil, errors.New("research_upgrade_failed")
	}
	clientPipe.SetDeadline(time.Time{})
	serverPipe.SetDeadline(time.Time{})
	client.SetReadLimit(wsReadLimit)
	server.SetReadLimit(wsReadLimit)
	bridge := &acceptanceBridge{upstream: upstream, server: server, client: client, done: make(chan struct{})}
	server.SetPingHandler(func(payload string) error {
		return upstream.WriteControl(websocket.PingMessage, []byte(payload), time.Now().Add(wsWriteTimeout))
	})
	upstream.SetPongHandler(func(payload string) error {
		return server.WriteControl(websocket.PongMessage, []byte(payload), time.Now().Add(wsWriteTimeout))
	})
	upstream.SetPingHandler(func(payload string) error {
		return server.WriteControl(websocket.PingMessage, []byte(payload), time.Now().Add(wsWriteTimeout))
	})
	server.SetPongHandler(func(payload string) error {
		return upstream.WriteControl(websocket.PongMessage, []byte(payload), time.Now().Add(wsWriteTimeout))
	})
	stop := context.AfterFunc(ctx, func() { bridge.end(0, false) })
	bridge.workers.Add(2)
	go bridge.pump(upstream, server)
	go bridge.pump(server, upstream)
	go func() { bridge.workers.Wait(); stop(); close(bridge.done) }()
	return bridge, nil
}

func (bridge *acceptanceBridge) pump(source, destination *websocket.Conn) {
	defer bridge.workers.Done()
	for {
		kind, payload, err := source.ReadMessage()
		if err != nil {
			code := 0
			var closeError *websocket.CloseError
			if errors.As(err, &closeError) && closeError.Code != 1006 && closeError.Code != 1005 {
				code = closeError.Code
			}
			bridge.end(code, false)
			return
		}
		destination.SetWriteDeadline(time.Now().Add(wsWriteTimeout))
		if destination.WriteMessage(kind, payload) != nil {
			bridge.end(0, false)
			return
		}
	}
}

func (bridge *acceptanceBridge) end(code int, triggered bool) bool {
	applied := false
	bridge.ending.Do(func() {
		applied = triggered
		bridge.triggered.Store(triggered)
		bridge.upstream.Close()
		if code != 0 {
			bridge.server.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(code, ""), time.Now().Add(time.Second))
		}
		bridge.server.Close()
	})
	return applied
}

func (session *Session) researchSignalingBoundary(upstream *websocket.Conn) (*websocket.Conn, error) {
	if roomHash, _ := session.ctx.Value(acceptanceKey{}).(string); len(roomHash) != 64 {
		return upstream, nil
	}
	bridge, err := newAcceptanceBridge(session.ctx, upstream)
	if err != nil {
		return nil, err
	}
	session.bridge.Store(bridge)
	return bridge.client, nil
}

func (session *Session) ResearchCloseSeed1011() bool {
	bridge := session.bridge.Load()
	if bridge == nil || session.ctx.Err() != nil || session.closed.Load() {
		return false
	}
	return bridge.end(websocket.CloseInternalServerErr, true)
}

func (session *Session) ResearchTriggerObserved() bool {
	bridge := session.bridge.Load()
	observed := session.SignalingReadFailure()
	return bridge != nil && bridge.triggered.Load() && observed.Kind == "WS_CLOSE" && observed.CloseCode == 1011 && observed.ContextState == "ACTIVE" && !observed.CarrierClosed
}

func (session *Session) ResearchRoomHash() string {
	if roomHash, ok := session.ctx.Value(acceptanceKey{}).(string); ok && len(roomHash) == 64 {
		return roomHash
	}
	digest := sha256.Sum256([]byte(session.cfg.RoomURL))
	return hex.EncodeToString(digest[:])
}
