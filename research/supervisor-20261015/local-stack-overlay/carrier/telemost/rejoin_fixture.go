//go:build sameroomfixture

package telemost

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"net"
	"net/url"
	"sync"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

var rejoinFixtureConfig struct {
	sync.RWMutex
	api, address string
	roots        *x509.CertPool
}

func (session *Session) RejoinFixtureRoomHash() [32]byte {
	return sha256.Sum256([]byte(session.roomID))
}

func ConfigureRejoinFixture(api, address string, roots *x509.CertPool) {
	parsed, err := url.Parse(api)
	if err != nil || parsed.Hostname() != "127.0.0.1" || parsed.Scheme != "https" {
		panic("fixture requires local TLS metadata")
	}
	rejoinFixtureConfig.Lock()
	defer rejoinFixtureConfig.Unlock()
	rejoinFixtureConfig.api, rejoinFixtureConfig.address, rejoinFixtureConfig.roots = api, address, roots
}

func rejoinFixtureAPIURL() string {
	rejoinFixtureConfig.RLock()
	defer rejoinFixtureConfig.RUnlock()
	if rejoinFixtureConfig.api == "" {
		return DefaultAPIURL
	}
	return rejoinFixtureConfig.api
}

func rejoinFixtureDialer(dialer websocket.Dialer) websocket.Dialer {
	rejoinFixtureConfig.RLock()
	address, roots := rejoinFixtureConfig.address, rejoinFixtureConfig.roots
	rejoinFixtureConfig.RUnlock()
	dialer.Proxy = nil
	dialer.TLSClientConfig = &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12}
	dialer.NetDialContext = func(ctx context.Context, network, destination string) (net.Conn, error) {
		if destination != "fixture.yandex.ru:443" {
			return nil, errors.New("fixture denies nonlocal dial")
		}
		return (&net.Dialer{}).DialContext(ctx, "tcp4", address)
	}
	return dialer
}

func (session *Session) RejoinFixtureOldCallbacks() {
	callback := session.iceHandler("SUBSCRIBER")
	callback(&webrtc.ICECandidate{Foundation: "local", Priority: 1, Address: "127.0.0.1", Protocol: webrtc.ICEProtocolUDP, Port: 9, Typ: webrtc.ICECandidateTypeHost, Component: 1})
	_ = session.writeJSON(map[string]any{"uid": "old-generation", "pong": map[string]any{}})
	session.onSubscriberState(webrtc.PeerConnectionStateClosed)
	session.onPublisherState(webrtc.PeerConnectionStateClosed)
	session.cancel()
	_ = session.Close()
}
