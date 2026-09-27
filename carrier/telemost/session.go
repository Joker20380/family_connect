package telemost

import (
	"context"
	"crypto/rand"
	"encoding/binary"
	"errors"
	"fmt"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/interceptor"
	"github.com/pion/webrtc/v4"
	"github.com/pion/webrtc/v4/pkg/media"
)

const (
	defaultSTUNURL = "stun:stun.rtc.yandex.net:3478"

	wsReadTimeout      = 60 * time.Second
	wsWriteTimeout     = 15 * time.Second
	wsHandshakeTimeout = 15 * time.Second
	wsReadLimit        = 8 << 20

	// vp8SendInterval paces consecutive data frames so the SFU is not
	// overwhelmed by back-to-back writes.
	vp8SendInterval = 2 * time.Millisecond
	// vp8KeepaliveInterval injects a decodable VP8 keyframe on a steady
	// cadence so the SFU decoder never times out and stops forwarding.
	vp8KeepaliveInterval = 2 * time.Second
	// vp8FrameDuration is the nominal duration reported for each VP8 sample.
	vp8FrameDuration = 33 * time.Millisecond

	// dcBufferedHighWaterMark pauses the data-channel writer when the buffered
	// amount crosses this threshold, providing simple backpressure.
	dcBufferedHighWaterMark = 1 << 20

	sendQueueSize = 256
)

// Mode selects the carrier transport.
type Mode int

const (
	// ModeVP8 carries bytes as VP8 video frames (primary Telemost path).
	ModeVP8 Mode = iota
	// ModeDataChannel carries bytes over a native data channel.
	ModeDataChannel
)

// String returns a stable, machine-readable mode name.
func (m Mode) String() string {
	switch m {
	case ModeVP8:
		return "vp8"
	case ModeDataChannel:
		return "datachannel"
	default:
		return "unknown"
	}
}

// Config configures a Telemost carrier session.
type Config struct {
	RoomURL     string
	DisplayName string
	Mode        Mode
	HTTPClient  *http.Client
	// Timeouts, zero means default.
	ConnectTimeout time.Duration
}

// Stats is a point-in-time snapshot of carrier metrics.
type Stats struct {
	Mode            string
	SetupMs         int64
	BytesSent       uint64
	BytesReceived   uint64
	MessagesSent    uint64
	MessagesRecv    uint64
	ReconnectCount  uint32
	SubscriberState string
	PublisherState  string
}

// Session owns one Telemost conference join and one carrier direction.
// It is not safe for concurrent Send; callers must serialise sends or use the
// isolated IPC process which already does.
type Session struct {
	cfg      Config
	mode     Mode
	senderID uint32

	auth *Auth

	peerID      string
	roomID      string
	credentials string
	wsURL       string

	// atomic generation handles for the two peer connections and data channel.
	pcSub atomic.Pointer[webrtc.PeerConnection]
	pcPub atomic.Pointer[webrtc.PeerConnection]
	dc    atomic.Pointer[webrtc.DataChannel]
	track *webrtc.TrackLocalStaticSample

	wsMu sync.Mutex
	ws   *websocket.Conn

	msgID       atomic.Uint32
	onDataMu    sync.RWMutex
	onData      func([]byte)
	reassembler *reassembler

	sendQueue chan []byte
	closeCh   chan struct{}
	closeOnce sync.Once
	closed    atomic.Bool

	subReady   atomic.Bool
	pubReady   atomic.Bool
	dcReady    chan struct{}
	connected  chan struct{}
	connectErr error

	reconnects atomic.Uint32

	statsMu      sync.Mutex
	bytesSent    uint64
	bytesRecv    uint64
	msgsSent     uint64
	msgsRecv     uint64
	setupStarted time.Time
	setupDone    time.Time

	wg sync.WaitGroup
}

// New creates an unconnected Session.
func New(ctx context.Context, cfg Config) (*Session, error) {
	if cfg.RoomURL == "" {
		return nil, errors.New("telemost: room URL required")
	}
	if cfg.ConnectTimeout <= 0 {
		cfg.ConnectTimeout = 60 * time.Second
	}
	s := &Session{
		cfg:        cfg,
		mode:       cfg.Mode,
		senderID:   randomUint32(),
		auth:       NewAuth(cfg.HTTPClient),
		sendQueue:  make(chan []byte, sendQueueSize),
		closeCh:    make(chan struct{}),
		connected:  make(chan struct{}),
		setupStarted: time.Now(),
	}
	s.msgID.Store(randomUint32())
	s.reassembler = newReassembler(s.senderID, s.deliver)
	return s, nil
}

// OnMessage registers the callback invoked with each reassembled message.
func (s *Session) OnMessage(cb func([]byte)) {
	s.onDataMu.Lock()
	s.onData = cb
	s.onDataMu.Unlock()
}

func (s *Session) deliver(payload []byte) {
	s.statsMu.Lock()
	s.bytesRecv += uint64(len(payload))
	s.msgsRecv++
	s.statsMu.Unlock()
	s.onDataMu.RLock()
	cb := s.onData
	s.onDataMu.RUnlock()
	if cb != nil {
		cb(payload)
	}
}

// Connect performs the join and blocks until the carrier is ready, ctx is
// cancelled, or the connect deadline expires.
func (s *Session) Connect(ctx context.Context) error {
	connCtx, cancel := context.WithTimeout(ctx, s.cfg.ConnectTimeout)
	defer cancel()

	info, err := s.auth.FetchConnection(connCtx, s.cfg.RoomURL, s.cfg.DisplayName)
	if err != nil {
		return err
	}
	s.peerID = info.PeerID
	s.roomID = info.RoomID
	s.credentials = info.Credentials
	s.wsURL = info.ClientConfig.MediaServerURL

	if err := s.setupPeerConnections(webrtc.Configuration{
		ICEServers:   []webrtc.ICEServer{{URLs: []string{defaultSTUNURL}}},
		SDPSemantics: webrtc.SDPSemanticsUnifiedPlan,
	}); err != nil {
		return err
	}

	if err := s.setupTransport(); err != nil {
		return err
	}
	if err := s.dialWebSocket(); err != nil {
		return err
	}
	s.setupICEHandlers()

	s.wg.Add(1)
	go s.signalingLoop()
	s.wg.Add(1)
	go s.writerLoop()

	if err := s.sendHello(); err != nil {
		return err
	}

	select {
	case <-s.connected:
		s.setupDone = time.Now()
		return nil
	case <-connCtx.Done():
		if connCtx.Err() == context.DeadlineExceeded {
			return fmt.Errorf("telemost: connect timeout after %s", s.cfg.ConnectTimeout)
		}
		return connCtx.Err()
	case <-s.closeCh:
		if s.connectErr != nil {
			return s.connectErr
		}
		return ErrClosed
	}
}

// Send delivers one application message to the remote peer.
func (s *Session) Send(payload []byte) error {
	if s.closed.Load() {
		return ErrClosed
	}
	if len(payload) > MaxMessageSize {
		return ErrMessageTooLarge
	}
	if !s.subReady.Load() && !s.pubReady.Load() && s.dcOpen() != nil {
		return errors.New("telemost: carrier not ready")
	}
	msgID := s.msgID.Add(1)
	frames, err := encodeFragments(s.senderID, msgID, payload)
	if err != nil {
		return err
	}
	for _, frag := range frames {
		out := frag
		if s.mode == ModeVP8 {
			out = encodeVP8DataFrame(frag)
		}
		select {
		case s.sendQueue <- out:
		case <-s.closeCh:
			return ErrClosed
		}
	}
	s.statsMu.Lock()
	s.bytesSent += uint64(len(payload))
	s.msgsSent++
	s.statsMu.Unlock()
	return nil
}

// Stats returns a metrics snapshot.
func (s *Session) Stats() Stats {
	s.statsMu.Lock()
	bs, br, ms, mr := s.bytesSent, s.bytesRecv, s.msgsSent, s.msgsRecv
	s.statsMu.Unlock()

	var setupMs int64
	if !s.setupDone.IsZero() {
		setupMs = s.setupDone.Sub(s.setupStarted).Milliseconds()
	}
	sub := "closed"
	if subPC := s.pcSub.Load(); subPC != nil {
		sub = subPC.ConnectionState().String()
	}
	pub := "closed"
	if pubPC := s.pcPub.Load(); pubPC != nil {
		pub = pubPC.ConnectionState().String()
	}
	return Stats{
		Mode:            s.mode.String(),
		SetupMs:         setupMs,
		BytesSent:       bs,
		BytesReceived:   br,
		MessagesSent:    ms,
		MessagesRecv:    mr,
		ReconnectCount:  s.reconnects.Load(),
		SubscriberState: sub,
		PublisherState:  pub,
	}
}

// Close tears down the session. It is idempotent.
func (s *Session) Close() error {
	s.closeOnce.Do(func() {
		s.closed.Store(true)
		close(s.closeCh)
	})

	s.wsMu.Lock()
	ws := s.ws
	s.ws = nil
	s.wsMu.Unlock()
	if ws != nil {
		_ = ws.WriteControl(websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""),
			time.Now().Add(time.Second))
		_ = ws.Close()
	}
	if dc := s.dc.Load(); dc != nil {
		_ = dc.Close()
	}
	for _, pc := range []*webrtc.PeerConnection{s.pcPub.Load(), s.pcSub.Load()} {
		if pc != nil {
			_ = pc.Close()
		}
	}
	done := make(chan struct{})
	go func() {
		s.wg.Wait()
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(3 * time.Second):
	}
	return nil
}

func (s *Session) dcOpen() *webrtc.DataChannel {
	if s.mode != ModeDataChannel {
		return nil
	}
	dc := s.dc.Load()
	if dc == nil || dc.ReadyState() != webrtc.DataChannelStateOpen {
		return nil
	}
	return dc
}

func (s *Session) setupPeerConnections(config webrtc.Configuration) error {
	api, err := newWebRTCAPI()
	if err != nil {
		return err
	}
	sub, err := api.NewPeerConnection(config)
	if err != nil {
		return fmt.Errorf("telemost: subscriber pc: %w", err)
	}
	sub.OnConnectionStateChange(s.onSubscriberState)
	sub.OnTrack(s.onSubscriberTrack)
	sub.OnDataChannel(s.onSubscriberDataChannel)
	s.pcSub.Store(sub)

	pub, err := api.NewPeerConnection(config)
	if err != nil {
		_ = sub.Close()
		return fmt.Errorf("telemost: publisher pc: %w", err)
	}
	pub.OnConnectionStateChange(s.onPublisherState)
	s.pcPub.Store(pub)
	return nil
}

func newWebRTCAPI() (*webrtc.API, error) {
	settings := webrtc.SettingEngine{}
	settings.SetNetworkTypes([]webrtc.NetworkType{webrtc.NetworkTypeUDP4})
	settings.SetIPFilter(func(ip net.IP) bool { return ip.To4() != nil })

	mediaEngine := &webrtc.MediaEngine{}
	if err := mediaEngine.RegisterDefaultCodecs(); err != nil {
		return nil, fmt.Errorf("telemost: register codecs: %w", err)
	}
	registry := &interceptor.Registry{}
	if err := webrtc.RegisterDefaultInterceptors(mediaEngine, registry); err != nil {
		return nil, fmt.Errorf("telemost: interceptors: %w", err)
	}
	return webrtc.NewAPI(
		webrtc.WithSettingEngine(settings),
		webrtc.WithMediaEngine(mediaEngine),
		webrtc.WithInterceptorRegistry(registry),
	), nil
}

// setupTransport attaches the mode-specific local media/data to the publisher.
func (s *Session) setupTransport() error {
	pub := s.pcPub.Load()
	if s.mode == ModeVP8 {
		track, err := newVP8Track()
		if err != nil {
			return fmt.Errorf("telemost: new vp8 track: %w", err)
		}
		if _, err := pub.AddTrack(track); err != nil {
			return fmt.Errorf("telemost: add vp8 track: %w", err)
		}
		s.track = track
		return nil
	}

	dc, err := pub.CreateDataChannel("fc-carrier", &webrtc.DataChannelInit{})
	if err != nil {
		return fmt.Errorf("telemost: create data channel: %w", err)
	}
	dc.OnOpen(func() {
		s.pubReady.Store(true)
		if s.dcReady != nil {
			close(s.dcReady)
		}
		s.maybeConnected()
	})
	dc.OnClose(func() {
		s.pubReady.Store(false)
	})
	dc.OnMessage(s.onDataChannelMessage)
	s.dc.Store(dc)
	s.dcReady = make(chan struct{})
	return nil
}

func (s *Session) onSubscriberTrack(track *webrtc.TrackRemote, receiver *webrtc.RTPReceiver) {
	if track.Kind() != webrtc.RTPCodecTypeVideo || track.Codec().MimeType != webrtc.MimeTypeVP8 {
		go drainTrack(track)
		return
	}
	go s.readVP8Track(track)
}

func (s *Session) onSubscriberDataChannel(dc *webrtc.DataChannel) {
	dc.OnMessage(s.onDataChannelMessage)
	dc.OnOpen(func() {
		s.subReady.Store(true)
		s.maybeConnected()
	})
}

func (s *Session) onDataChannelMessage(msg webrtc.DataChannelMessage) {
	if len(msg.Data) == 0 {
		return
	}
	s.reassembler.ingest(msg.Data)
}

func drainTrack(track *webrtc.TrackRemote) {
	buf := make([]byte, 1500)
	for {
		if _, _, err := track.Read(buf); err != nil {
			return
		}
	}
}

func (s *Session) maybeConnected() {
	switch s.mode {
	case ModeVP8:
		if s.subReady.Load() && s.pubReady.Load() {
			select {
			case <-s.connected:
			default:
				close(s.connected)
			}
		}
	case ModeDataChannel:
		if s.dcOpen() != nil && s.subReady.Load() {
			select {
			case <-s.connected:
			default:
				close(s.connected)
			}
		}
	}
}

func (s *Session) onSubscriberState(state webrtc.PeerConnectionState) {
	switch state {
	case webrtc.PeerConnectionStateConnected:
		s.subReady.Store(true)
		s.maybeConnected()
	case webrtc.PeerConnectionStateDisconnected,
		webrtc.PeerConnectionStateFailed,
		webrtc.PeerConnectionStateClosed:
		s.subReady.Store(false)
	}
}

func (s *Session) onPublisherState(state webrtc.PeerConnectionState) {
	switch state {
	case webrtc.PeerConnectionStateConnected:
		s.pubReady.Store(true)
		s.maybeConnected()
	case webrtc.PeerConnectionStateDisconnected,
		webrtc.PeerConnectionStateFailed,
		webrtc.PeerConnectionStateClosed:
		s.pubReady.Store(false)
	}
}

func randomUint32() uint32 {
	var b [4]byte
	if _, err := rand.Read(b[:]); err != nil {
		return uint32(time.Now().UnixNano())
	}
	v := binary.BigEndian.Uint32(b[:])
	if v == 0 {
		v = 1
	}
	return v
}
