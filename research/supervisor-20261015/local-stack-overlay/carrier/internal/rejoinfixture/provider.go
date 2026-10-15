//go:build sameroomfixture

package rejoinfixture

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/subtle"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"math/big"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/gorilla/websocket"
	"github.com/pion/logging"
	"github.com/pion/rtp"
	"github.com/pion/webrtc/v4"
)

type Provider struct {
	mu                                   sync.Mutex
	server                               *httptest.Server
	rooms                                map[string]*Room
	peers                                map[string]*Peer
	joins, creates, active, peak, tx, rx atomic.Int64
	pcs                                  atomic.Int64
	seedOwners, peakSeedOwners           atomic.Int64
	transcript                           []Event
	mode                                 string
}

type Event struct {
	Kind       string `json:"kind"`
	Generation string `json:"generation"`
	Target     string `json:"target,omitempty"`
	State      string `json:"state,omitempty"`
}

type Room struct {
	id      string
	until   time.Time
	deleted bool
	slots   [4]*Peer
}

type Peer struct {
	provider             *Provider
	room                 *Room
	id, label            string
	credential           string
	credentialUntil      time.Time
	slot                 int
	ws                   *websocket.Conn
	writeMu              sync.Mutex
	once                 sync.Once
	done                 chan struct{}
	toClient, fromClient *webrtc.PeerConnection
	tracks               [4]*webrtc.TrackLocalStaticRTP
	pending              map[string][]webrtc.ICECandidateInit
	workers              sync.WaitGroup
}

func Start(test *testing.T) *Provider {
	test.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		test.Fatal(err)
	}
	template := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "disposable local fixture"},
		NotBefore: time.Now().Add(-time.Minute), NotAfter: time.Now().Add(time.Hour),
		DNSNames: []string{"fixture.yandex.ru"}, IPAddresses: []net.IP{net.ParseIP("127.0.0.1")},
		IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		test.Fatal(err)
	}
	encoded, _ := x509.MarshalPKCS8PrivateKey(key)
	certificate, err := tls.X509KeyPair(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: encoded}))
	if err != nil {
		test.Fatal(err)
	}
	roots := x509.NewCertPool()
	parsed, _ := x509.ParseCertificate(der)
	roots.AddCert(parsed)
	provider := &Provider{rooms: map[string]*Room{}, peers: map[string]*Peer{}}
	server := httptest.NewUnstartedServer(http.HandlerFunc(provider.serve))
	server.TLS = &tls.Config{Certificates: []tls.Certificate{certificate}, MinVersion: tls.VersionTLS12}
	server.StartTLS()
	provider.server = server
	oldTransport := http.DefaultTransport
	transport := oldTransport.(*http.Transport).Clone()
	transport.Proxy = nil
	transport.TLSClientConfig = &tls.Config{RootCAs: roots, MinVersion: tls.VersionTLS12}
	transport.DialContext = func(ctx context.Context, network, address string) (net.Conn, error) {
		if address != server.Listener.Addr().String() {
			return nil, errors.New("fixture denies external HTTP dial")
		}
		return (&net.Dialer{}).DialContext(ctx, "tcp4", address)
	}
	http.DefaultTransport = transport
	telemost.ConfigureRejoinFixture(server.URL, server.Listener.Addr().String(), roots)
	test.Cleanup(func() { provider.Close(); transport.CloseIdleConnections(); http.DefaultTransport = oldTransport })
	return provider
}

func (provider *Provider) event(event Event) {
	provider.mu.Lock()
	defer provider.mu.Unlock()
	if len(provider.transcript) < 4096 {
		provider.transcript = append(provider.transcript, event)
	}
}

func (provider *Provider) CreateRoom(ctx context.Context) (roombroker.Room, error) {
	if ctx.Err() != nil {
		return roombroker.Room{}, ctx.Err()
	}
	provider.mu.Lock()
	defer provider.mu.Unlock()
	identifier := "local-room-" + strconv.FormatInt(provider.creates.Add(1), 10)
	provider.rooms[identifier] = &Room{id: identifier, until: time.Now().Add(30 * time.Minute)}
	return roombroker.Room{JoinURL: "https://telemost.yandex.ru/j/" + identifier, ID: identifier}, nil
}

func (provider *Provider) serve(writer http.ResponseWriter, request *http.Request) {
	if strings.HasPrefix(request.URL.Path, "/peer/") {
		provider.mu.Lock()
		peer := provider.peers[strings.TrimPrefix(request.URL.Path, "/peer/")]
		provider.mu.Unlock()
		if peer == nil {
			http.Error(writer, "not found", 404)
			return
		}
		connection, err := (&websocket.Upgrader{CheckOrigin: func(*http.Request) bool { return true }}).Upgrade(writer, request, nil)
		if err != nil {
			return
		}
		provider.mu.Lock()
		peer.ws = connection
		provider.mu.Unlock()
		peer.run()
		return
	}
	if request.Method != http.MethodGet || !strings.HasPrefix(request.URL.Path, "/conferences/") {
		http.Error(writer, "rejected", 400)
		return
	}
	full := strings.TrimSuffix(strings.TrimPrefix(request.URL.Path, "/conferences/"), "/connection")
	parsed, err := url.Parse(full)
	if err != nil {
		http.Error(writer, "rejected", 400)
		return
	}
	identifier := strings.TrimPrefix(parsed.Path, "/j/")
	provider.mu.Lock()
	room := provider.rooms[identifier]
	if provider.mode == "metadata_unavailable" {
		provider.mu.Unlock()
		http.Error(writer, "unavailable", 503)
		return
	}
	if room == nil || room.deleted || !time.Now().Before(room.until) {
		provider.mu.Unlock()
		http.Error(writer, "rejected", 403)
		return
	}
	slot := -1
	for index, peer := range room.slots {
		if peer == nil {
			slot = index
			break
		}
	}
	if slot < 0 {
		provider.mu.Unlock()
		http.Error(writer, "bounded", 429)
		return
	}
	peer := &Peer{provider: provider, room: room, id: fmt.Sprint(provider.joins.Add(1)), label: request.URL.Query().Get("display_name"), slot: slot, done: make(chan struct{}), pending: map[string][]webrtc.ICECandidateInit{}}
	var secret [32]byte
	if _, err := rand.Read(secret[:]); err != nil {
		provider.mu.Unlock()
		http.Error(writer, "unavailable", 503)
		return
	}
	peer.credential = hex.EncodeToString(secret[:])
	peer.credentialUntil = minTime(room.until, time.Now().Add(15*time.Minute))
	if provider.mode == "join_credential_expired" {
		peer.credentialUntil = time.Now().Add(-time.Second)
	}
	room.slots[slot] = peer
	provider.peers[peer.id] = peer
	provider.mu.Unlock()
	json.NewEncoder(writer).Encode(map[string]any{"room_id": identifier, "peer_id": peer.id, "credentials": peer.credential, "client_configuration": map[string]any{"media_server_url": "wss://fixture.yandex.ru/peer/" + peer.id}})
}

func minTime(first, second time.Time) time.Time {
	if first.Before(second) {
		return first
	}
	return second
}

func (peer *Peer) write(message map[string]any) error {
	peer.writeMu.Lock()
	defer peer.writeMu.Unlock()
	_ = peer.ws.SetWriteDeadline(time.Now().Add(3 * time.Second))
	return peer.ws.WriteJSON(message)
}

func newPC() (*webrtc.PeerConnection, error) {
	settings := webrtc.SettingEngine{}
	settings.SetNetworkTypes([]webrtc.NetworkType{webrtc.NetworkTypeUDP4})
	logger := logging.NewDefaultLoggerFactory()
	logger.Writer = io.Discard
	settings.LoggerFactory = logger
	return webrtc.NewAPI(webrtc.WithSettingEngine(settings)).NewPeerConnection(webrtc.Configuration{})
}

func (peer *Peer) setup() error {
	var err error
	peer.toClient, err = newPC()
	if err != nil {
		return err
	}
	peer.provider.pcs.Add(1)
	peer.fromClient, err = newPC()
	if err != nil {
		return err
	}
	peer.provider.pcs.Add(1)
	for index := range peer.tracks {
		track, err := webrtc.NewTrackLocalStaticRTP(webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8, ClockRate: 90000}, fmt.Sprint("slot", index), "local-sfu")
		if err != nil {
			return err
		}
		peer.provider.mu.Lock()
		peer.tracks[index] = track
		peer.provider.mu.Unlock()
		sender, err := peer.toClient.AddTrack(track)
		if err != nil {
			return err
		}
		peer.workers.Add(1)
		go func() {
			defer peer.workers.Done()
			buffer := make([]byte, 1500)
			for {
				if _, _, err := sender.Read(buffer); err != nil {
					return
				}
			}
		}()
	}
	for target, connection := range map[string]*webrtc.PeerConnection{"SUBSCRIBER": peer.toClient, "PUBLISHER": peer.fromClient} {
		connection.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
			peer.provider.event(Event{"PC", peer.id, target, state.String()})
		})
		connection.OnICEConnectionStateChange(func(state webrtc.ICEConnectionState) {
			peer.provider.event(Event{"ICE", peer.id, target, state.String()})
		})
		connection.OnICECandidate(func(candidate *webrtc.ICECandidate) {
			if candidate == nil {
				return
			}
			peer.provider.mu.Lock()
			mode := peer.provider.mode
			peer.provider.mu.Unlock()
			if mode == "ice_failure" {
				return
			}
			value := candidate.ToJSON()
			_ = peer.write(map[string]any{"uid": "local-ice", "webrtcIceCandidate": map[string]any{"target": target, "candidate": value.Candidate, "sdpMid": value.SDPMid, "sdpMlineIndex": value.SDPMLineIndex, "pcSeq": 1}})
		})
	}
	peer.fromClient.OnTrack(func(track *webrtc.TrackRemote, _ *webrtc.RTPReceiver) {
		peer.workers.Add(1)
		defer peer.workers.Done()
		for {
			packet, _, err := track.ReadRTP()
			if err != nil {
				return
			}
			peer.provider.rx.Add(1)
			peer.forward(packet)
		}
	})
	return nil
}

func (peer *Peer) forward(packet *rtp.Packet) {
	peer.provider.mu.Lock()
	tracks := make([]*webrtc.TrackLocalStaticRTP, 0, 3)
	for _, other := range peer.room.slots {
		if other != nil && other != peer && other.tracks[peer.slot] != nil {
			tracks = append(tracks, other.tracks[peer.slot])
		}
	}
	peer.provider.mu.Unlock()
	for _, track := range tracks {
		if track.WriteRTP(packet) == nil {
			peer.provider.tx.Add(1)
		}
	}
}

func (peer *Peer) remote(target string, description webrtc.SessionDescription) error {
	connection := peer.toClient
	if target == "PUBLISHER" {
		connection = peer.fromClient
	}
	if err := connection.SetRemoteDescription(description); err != nil {
		return err
	}
	for _, candidate := range peer.pending[target] {
		if err := connection.AddICECandidate(candidate); err != nil {
			return err
		}
	}
	delete(peer.pending, target)
	return nil
}

func (peer *Peer) run() {
	if peer.label == "Family bootstrap gateway" {
		owners := peer.provider.seedOwners.Add(1)
		for {
			peak := peer.provider.peakSeedOwners.Load()
			if owners <= peak || peer.provider.peakSeedOwners.CompareAndSwap(peak, owners) {
				break
			}
		}
	}
	active := peer.provider.active.Add(1)
	for {
		old := peer.provider.peak.Load()
		if active <= old || peer.provider.peak.CompareAndSwap(old, active) {
			break
		}
	}
	defer peer.close()
	if err := peer.setup(); err != nil {
		return
	}
	for {
		var message map[string]json.RawMessage
		if peer.ws.ReadJSON(&message) != nil {
			return
		}
		for kind := range message {
			if kind != "uid" {
				peer.provider.event(Event{Kind: "RX_" + kind, Generation: peer.id})
			}
		}
		if hello, ok := message["hello"]; ok {
			var claims struct {
				Participant string `json:"participantId"`
				Room        string `json:"roomId"`
				Credential  string `json:"credentials"`
			}
			if json.Unmarshal(hello, &claims) != nil || claims.Participant != peer.id || claims.Room != peer.room.id || subtle.ConstantTimeCompare([]byte(claims.Credential), []byte(peer.credential)) != 1 || !time.Now().Before(peer.credentialUntil) {
				_ = peer.ws.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(1008, ""), time.Now().Add(time.Second))
				continue
			}
			_ = peer.write(map[string]any{"uid": "hello", "serverHello": map[string]any{}})
			peer.provider.mu.Lock()
			mode := peer.provider.mode
			peer.provider.mu.Unlock()
			if mode == "media_never_ready" {
				continue
			}
			if mode == "close1011" {
				_ = peer.ws.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(1011, ""), time.Now().Add(time.Second))
				continue
			}
			if mode == "malformed" {
				peer.writeMu.Lock()
				_ = peer.ws.WriteMessage(websocket.TextMessage, []byte("{\"invalid\":]}"))
				peer.writeMu.Unlock()
				continue
			}
			if mode == "policy" {
				_ = peer.ws.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(1008, ""), time.Now().Add(time.Second))
				continue
			}
			if mode == "protocol" {
				_ = peer.ws.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(1002, ""), time.Now().Add(time.Second))
				continue
			}
			offer, err := peer.toClient.CreateOffer(nil)
			if err != nil {
				return
			}
			if peer.toClient.SetLocalDescription(offer) != nil {
				return
			}
			sdp := offer.SDP
			if mode == "bad_sdp" {
				sdp = "invalid-local-sdp"
			}
			if peer.write(map[string]any{"uid": "offer", "subscriberSdpOffer": map[string]any{"pcSeq": 1, "sdp": sdp}}) != nil {
				return
			}
		}
		if raw, ok := message["subscriberSdpAnswer"]; ok {
			var value struct {
				SDP string `json:"sdp"`
			}
			if json.Unmarshal(raw, &value) != nil {
				return
			}
			if peer.remote("SUBSCRIBER", webrtc.SessionDescription{Type: webrtc.SDPTypeAnswer, SDP: value.SDP}) != nil {
				return
			}
		}
		if raw, ok := message["publisherSdpOffer"]; ok {
			var value struct {
				SDP string `json:"sdp"`
			}
			if json.Unmarshal(raw, &value) != nil {
				return
			}
			if peer.remote("PUBLISHER", webrtc.SessionDescription{Type: webrtc.SDPTypeOffer, SDP: value.SDP}) != nil {
				return
			}
			answer, err := peer.fromClient.CreateAnswer(nil)
			if err != nil {
				return
			}
			if peer.fromClient.SetLocalDescription(answer) != nil {
				return
			}
			if peer.write(map[string]any{"uid": "answer", "publisherSdpAnswer": map[string]any{"pcSeq": 1, "sdp": answer.SDP}}) != nil {
				return
			}
		}
		if raw, ok := message["webrtcIceCandidate"]; ok {
			peer.provider.mu.Lock()
			mode := peer.provider.mode
			peer.provider.mu.Unlock()
			if mode == "ice_failure" {
				continue
			}
			var value struct {
				Target        string  `json:"target"`
				Candidate     string  `json:"candidate"`
				SDPMid        *string `json:"sdpMid"`
				SDPMLineIndex *uint16 `json:"sdpMlineIndex"`
			}
			if json.Unmarshal(raw, &value) != nil {
				return
			}
			candidate := webrtc.ICECandidateInit{Candidate: value.Candidate, SDPMid: value.SDPMid, SDPMLineIndex: value.SDPMLineIndex}
			connection := peer.toClient
			if value.Target == "PUBLISHER" {
				connection = peer.fromClient
			}
			if connection.RemoteDescription() == nil {
				peer.pending[value.Target] = append(peer.pending[value.Target], candidate)
			} else if connection.AddICECandidate(candidate) != nil {
				return
			}
		}
		if _, ok := message["ping"]; ok {
			_ = peer.write(map[string]any{"uid": "pong", "pong": map[string]any{}})
		}
	}
}

func (peer *Peer) close() {
	peer.once.Do(func() {
		peer.provider.mu.Lock()
		if peer.room.slots[peer.slot] == peer {
			peer.room.slots[peer.slot] = nil
		}
		peer.provider.mu.Unlock()
		if peer.ws != nil {
			_ = peer.ws.Close()
		}
		if peer.toClient != nil {
			_ = peer.toClient.Close()
			peer.provider.pcs.Add(-1)
		}
		if peer.fromClient != nil {
			_ = peer.fromClient.Close()
			peer.provider.pcs.Add(-1)
		}
		peer.workers.Wait()
		peer.provider.active.Add(-1)
		if peer.label == "Family bootstrap gateway" {
			peer.provider.seedOwners.Add(-1)
		}
		peer.provider.mu.Lock()
		delete(peer.provider.peers, peer.id)
		peer.provider.mu.Unlock()
		close(peer.done)
	})
}

func (provider *Provider) CloseSeed(code int) (string, error) {
	provider.mu.Lock()
	var selected *Peer
	for _, peer := range provider.peers {
		if peer.label == "Family bootstrap gateway" {
			selected = peer
			break
		}
	}
	provider.mu.Unlock()
	if selected == nil {
		return "", errors.New("seed peer absent")
	}
	selected.writeMu.Lock()
	err := selected.ws.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(code, ""), time.Now().Add(time.Second))
	selected.writeMu.Unlock()
	return selected.id, err
}

func (provider *Provider) SetMode(mode string) {
	provider.mu.Lock()
	provider.mode = mode
	provider.mu.Unlock()
}
func (provider *Provider) SetRoomInvalid(join string, expired bool) {
	provider.mu.Lock()
	defer provider.mu.Unlock()
	room := provider.rooms[strings.TrimPrefix(join, "https://telemost.yandex.ru/j/")]
	if expired {
		room.until = time.Now().Add(-time.Second)
	} else {
		room.deleted = true
	}
}
func (provider *Provider) Snapshot() map[string]any {
	provider.mu.Lock()
	defer provider.mu.Unlock()
	return map[string]any{"room_creates": provider.creates.Load(), "joins": provider.joins.Load(), "retained_peers": len(provider.peers), "active_websockets": provider.active.Load(), "peer_connections": provider.pcs.Load(), "peak_websockets": provider.peak.Load(), "peak_seed_owners": provider.peakSeedOwners.Load(), "rtp_received": provider.rx.Load(), "rtp_forwarded": provider.tx.Load(), "events": append([]Event(nil), provider.transcript...)}
}

func (provider *Provider) WaitRetired(ctx context.Context, id string) error {
	ticker := time.NewTicker(time.Millisecond)
	defer ticker.Stop()
	for {
		provider.mu.Lock()
		_, exists := provider.peers[id]
		provider.mu.Unlock()
		if !exists {
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
		}
	}
}
func (provider *Provider) Close() {
	provider.mu.Lock()
	peers := make([]*Peer, 0, len(provider.peers))
	for _, peer := range provider.peers {
		peers = append(peers, peer)
	}
	provider.mu.Unlock()
	for _, peer := range peers {
		if peer.ws != nil {
			_ = peer.ws.Close()
		}
	}
	for _, peer := range peers {
		select {
		case <-peer.done:
		case <-time.After(5 * time.Second):
		}
	}
	provider.server.Close()
}

func (provider *Provider) SeedIDForAcceptance() string {
	provider.mu.Lock()
	defer provider.mu.Unlock()
	for _, peer := range provider.peers {
		if peer.label == "Family bootstrap gateway" {
			return peer.id
		}
	}
	return ""
}
