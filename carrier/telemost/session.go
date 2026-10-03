package telemost

import (
	"context"
	"crypto/rand"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/gorilla/websocket"
	"github.com/pion/interceptor"
	"github.com/pion/logging"
	"github.com/pion/webrtc/v4"
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
	Trace       *sessiontrace.Recorder
	RoomURL     string
	DisplayName string
	Mode        Mode
	HTTPClient  *http.Client
	Underlay    *underlay.Network
	// Timeouts, zero means default.
	ConnectTimeout time.Duration
	MaxVideoTracks int
}

// Stats is a point-in-time snapshot of carrier metrics.
type Stats struct {
	SendQueueDepth    int
	ReceiveQueueDepth int
	Mode              string
	SetupMs           int64
	BytesSent         uint64
	BytesReceived     uint64
	MessagesSent      uint64
	MessagesRecv      uint64
	ReconnectCount    uint32
	Disconnects       uint32
	SubscriberState   string
	PublisherState    string
	Evidence          []Evidence
	EvidenceDropped   uint64
	Media             MediaStats
	ApplicationPongs  uint64
	ApplicationPings  uint64
	SignalingACKs     uint64
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
	pcSub         atomic.Pointer[webrtc.PeerConnection]
	pcPub         atomic.Pointer[webrtc.PeerConnection]
	dc            atomic.Pointer[webrtc.DataChannel]
	track         *webrtc.TrackLocalStaticSample
	ctx           context.Context
	cancel        context.CancelFunc
	initMu        sync.Mutex
	workersMu     sync.Mutex
	started       atomic.Bool
	cleanupOnce   sync.Once
	cleanupDone   chan struct{}
	connectedOnce sync.Once
	errMu         sync.Mutex
	recvQueue     chan []byte
	disconnects   atomic.Uint32
	pendingICE    map[string][]webrtc.ICECandidateInit

	wsMu sync.Mutex
	ws   *websocket.Conn

	msgID       atomic.Uint32
	subSequence atomic.Uint32
	reassembler *reassembler

	sendQueue chan []byte
	closeCh   chan struct{}
	closeOnce sync.Once
	closed    atomic.Bool

	subReady   atomic.Bool
	pubReady   atomic.Bool
	connected  chan struct{}
	connectErr error

	reconnects  atomic.Uint32
	videoTracks atomic.Int32

	statsMu          sync.Mutex
	bytesSent        uint64
	bytesRecv        uint64
	msgsSent         uint64
	msgsRecv         uint64
	setupStarted     time.Time
	setupDone        time.Time
	evidence         []Evidence
	evidenceDropped  uint64
	mediaStats       MediaStats
	applicationPongs uint64
	applicationPings uint64
	signalingACKs    uint64

	wg sync.WaitGroup
}

// New creates an unconnected Session.
func New(ctx context.Context, cfg Config) (*Session, error) {
	if cfg.Trace == nil {
		cfg.Trace = sessiontrace.From(ctx)
	}
	if cfg.Underlay != nil {
		cfg.HTTPClient = cfg.Underlay.HTTPClient()
	}
	if cfg.MaxVideoTracks < 0 || cfg.MaxVideoTracks > 4 {
		return nil, errors.New("telemost: invalid track limit")
	}
	if !validRoom(cfg.RoomURL) {
		return nil, errors.New("telemost: invalid room URL")
	}
	if cfg.Mode != ModeVP8 && cfg.Mode != ModeDataChannel {
		return nil, errors.New("telemost: unsupported mode")
	}
	if cfg.ConnectTimeout <= 0 {
		cfg.ConnectTimeout = 60 * time.Second
	}
	s := &Session{
		cfg:          cfg,
		mode:         cfg.Mode,
		senderID:     randomUint32(),
		auth:         NewAuth(cfg.HTTPClient),
		sendQueue:    make(chan []byte, sendQueueSize),
		closeCh:      make(chan struct{}),
		connected:    make(chan struct{}),
		setupStarted: time.Now(),
	}
	s.msgID.Store(randomUint32())
	s.subSequence.Store(1)
	s.ctx, s.cancel = context.WithCancel(ctx)
	s.cleanupDone = make(chan struct{})
	s.recvQueue = make(chan []byte, 16)
	s.pendingICE = make(map[string][]webrtc.ICECandidateInit)
	s.reassembler = newReassembler(s.senderID, s.deliver)
	go func() { <-s.ctx.Done(); _ = s.Close() }()
	return s, nil
}

func (s *Session) deliver(payload []byte) {
	s.statsMu.Lock()
	s.bytesRecv += uint64(len(payload))
	s.msgsRecv++
	s.statsMu.Unlock()
	select {
	case s.recvQueue <- payload:
	case <-s.closeCh:
	default:
		s.signalClosed(errors.New("telemost: receive queue full"))
	}
}

func (s *Session) Recv(ctx context.Context) ([]byte, error) {
	select {
	case <-s.closeCh:
		return nil, s.failure()
	default:
	}
	select {
	case payload := <-s.recvQueue:
		return payload, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-s.closeCh:
		return nil, s.failure()
	}
}

// Connect performs the join and blocks until the carrier is ready, ctx is
// cancelled, or the connect deadline expires.
func (s *Session) Connect(ctx context.Context) (connectError error) {
	s.cfg.Trace.Add("CARRIER", "STARTED", "NONE")
	stage, reason := "GATEWAY_JOIN", "RECOVERY_JOIN_FAILED"
	if !s.started.CompareAndSwap(false, true) {
		return errors.New("telemost: connect already attempted")
	}
	s.initMu.Lock()
	defer func() {
		s.initMu.Unlock()
		if connectError != nil {
			if ctx.Err() != context.Canceled {
				s.cfg.Trace.Add(stage, "FAILED", reason)
			}
			_ = s.Close()
		}
	}()
	if s.closed.Load() {
		return ErrClosed
	}
	connCtx, cancel := context.WithTimeout(ctx, s.cfg.ConnectTimeout)
	defer cancel()
	stopCancel := context.AfterFunc(s.ctx, cancel)
	defer stopCancel()

	info, err := s.auth.FetchConnection(connCtx, s.cfg.RoomURL, s.cfg.DisplayName)
	if err != nil {
		return err
	}
	s.recordEvidence(Evidence{Stage: "ROOM_RESOLVED"})
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
	if err := s.dialWebSocket(connCtx); err != nil {
		return err
	}
	s.recordEvidence(Evidence{Stage: "SIGNALING_CONNECTED"})
	s.setupICEHandlers()

	s.startWorker(s.signalingLoop)
	s.startWorker(s.writerLoop)
	s.startWorker(s.heartbeatLoop)
	s.startWorker(func() {
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-s.closeCh:
				return
			case <-ticker.C:
				s.reassembler.prune()
			}
		}
	})

	if err := s.sendHello(); err != nil {
		return err
	}
	stage, reason = "CARRIER", "RECOVERY_CARRIER_FAILED"

	select {
	case <-s.connected:
		if s.closed.Load() {
			return s.failure()
		}
		s.statsMu.Lock()
		s.setupDone = time.Now()
		s.statsMu.Unlock()
		return nil
	case <-connCtx.Done():
		if connCtx.Err() == context.DeadlineExceeded {
			return fmt.Errorf("telemost: connect timeout after %s", s.cfg.ConnectTimeout)
		}
		return connCtx.Err()
	case <-s.closeCh:
		return s.failure()
	}
}

// Send delivers one application message to the remote peer.
func (s *Session) Send(payload []byte) error {
	ctx, cancel := context.WithTimeout(s.ctx, 10*time.Second)
	defer cancel()
	return s.SendContext(ctx, payload)
}

func (s *Session) SendContext(ctx context.Context, payload []byte) error {
	if s.closed.Load() {
		return ErrClosed
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if len(payload) > MaxMessageSize {
		return ErrMessageTooLarge
	}
	if !s.subReady.Load() || !s.pubReady.Load() || (s.mode == ModeDataChannel && s.dcOpen() == nil) {
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
		case <-ctx.Done():
			return ctx.Err()
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
	setupDone := s.setupDone
	evidence := append([]Evidence(nil), s.evidence...)
	for index := range evidence {
		evidence[index].ReasonKeywords = append([]string(nil), evidence[index].ReasonKeywords...)
		if evidence[index].TURNUsed != nil {
			relay := *evidence[index].TURNUsed
			evidence[index].TURNUsed = &relay
		}
	}
	evidenceDropped := s.evidenceDropped
	mediaStats := s.mediaStats
	applicationPongs := s.applicationPongs
	applicationPings := s.applicationPings
	signalingACKs := s.signalingACKs
	s.statsMu.Unlock()

	var setupMs int64
	if !setupDone.IsZero() {
		setupMs = setupDone.Sub(s.setupStarted).Milliseconds()
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
		SendQueueDepth:    len(s.sendQueue),
		ReceiveQueueDepth: len(s.recvQueue),
		Mode:              s.mode.String(),
		SetupMs:           setupMs,
		BytesSent:         bs,
		BytesReceived:     br,
		MessagesSent:      ms,
		MessagesRecv:      mr,
		ReconnectCount:    s.reconnects.Load(),
		Disconnects:       s.disconnects.Load(),
		SubscriberState:   sub,
		PublisherState:    pub,
		Evidence:          evidence,
		EvidenceDropped:   evidenceDropped,
		Media:             mediaStats,
		ApplicationPongs:  applicationPongs,
		ApplicationPings:  applicationPings,
		SignalingACKs:     signalingACKs,
	}
}

// Close tears down the session. It is idempotent.
func (s *Session) Close() error {
	s.cfg.Trace.Add("LOCAL_CLOSE", "STARTED", "NONE")
	defer s.cfg.Trace.Add("CLEANUP", "COMPLETED", "NONE")
	s.signalClosed(ErrClosed)
	s.cleanupOnce.Do(func() {
		s.initMu.Lock()
		defer s.initMu.Unlock()
		s.workersMu.Lock()
		s.workersMu.Unlock()
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
		s.wg.Wait()
		s.auth.closeIdleConnections()
		close(s.cleanupDone)
	})
	<-s.cleanupDone
	return nil
}

func (s *Session) startWorker(work func()) {
	s.workersMu.Lock()
	defer s.workersMu.Unlock()
	if s.closed.Load() {
		return
	}
	s.wg.Add(1)
	go func() { defer s.wg.Done(); work() }()
}

func (s *Session) failure() error {
	s.errMu.Lock()
	defer s.errMu.Unlock()
	if s.connectErr != nil {
		return s.connectErr
	}
	return ErrClosed
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
	api, err := newWebRTCAPI(s.cfg.Underlay)
	if err != nil {
		return err
	}
	sub, err := api.NewPeerConnection(config)
	if err != nil {
		return fmt.Errorf("telemost: subscriber pc: %w", err)
	}
	sub.OnConnectionStateChange(s.onSubscriberState)
	sub.OnICEConnectionStateChange(func(state webrtc.ICEConnectionState) { s.traceICE("SUBSCRIBER", state) })
	sub.OnTrack(s.onSubscriberTrack)
	sub.OnDataChannel(s.onSubscriberDataChannel)
	s.pcSub.Store(sub)

	pub, err := api.NewPeerConnection(config)
	if err != nil {
		_ = sub.Close()
		return fmt.Errorf("telemost: publisher pc: %w", err)
	}
	pub.OnConnectionStateChange(s.onPublisherState)
	pub.OnICEConnectionStateChange(func(state webrtc.ICEConnectionState) { s.traceICE("PUBLISHER", state) })
	s.pcPub.Store(pub)
	return nil
}

func newWebRTCAPI(networks ...*underlay.Network) (*webrtc.API, error) {
	settings := webrtc.SettingEngine{}
	if len(networks) > 0 && networks[0] != nil {
		settings.SetNet(networks[0])
	}
	logger := logging.NewDefaultLoggerFactory()
	logger.Writer = io.Discard
	settings.LoggerFactory = logger
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
		sender, err := pub.AddTrack(track)
		if err != nil {
			return fmt.Errorf("telemost: add vp8 track: %w", err)
		}
		s.track = track
		s.startWorker(func() {
			buffer := make([]byte, 1500)
			for {
				if _, _, err := sender.Read(buffer); err != nil {
					s.traceCarrierReadEnd("PUBLISHER", err)
					return
				}
			}
		})
		return nil
	}

	dc, err := pub.CreateDataChannel("fc-carrier", &webrtc.DataChannelInit{})
	if err != nil {
		return fmt.Errorf("telemost: create data channel: %w", err)
	}
	dc.OnOpen(func() {
		s.pubReady.Store(true)
		s.maybeConnected()
	})
	dc.OnClose(func() {
		s.pubReady.Store(false)
	})
	dc.OnMessage(s.onDataChannelMessage)
	s.dc.Store(dc)
	return nil
}

func (s *Session) onSubscriberTrack(track *webrtc.TrackRemote, receiver *webrtc.RTPReceiver) {
	if s.cfg.MaxVideoTracks > 0 {
		if track.Kind() != webrtc.RTPCodecTypeVideo || track.Codec().MimeType != webrtc.MimeTypeVP8 || s.videoTracks.Add(1) > int32(s.cfg.MaxVideoTracks) {
			if track.Kind() == webrtc.RTPCodecTypeVideo && track.Codec().MimeType == webrtc.MimeTypeVP8 {
				s.videoTracks.Add(-1)
			}
			_ = receiver.Stop()
			return
		}
		s.startWorker(func() { defer s.videoTracks.Add(-1); s.readVP8Track(track) })
		return
	}
	if s.mode != ModeVP8 || track.Kind() != webrtc.RTPCodecTypeVideo || track.Codec().MimeType != webrtc.MimeTypeVP8 {
		s.startWorker(func() { drainTrack(track) })
		return
	}
	s.recordEvidence(Evidence{Stage: "VP8_MEDIA_ACTIVE", Target: "SUBSCRIBER"})
	s.startWorker(func() { s.readVP8Track(track) })
}

func (s *Session) onSubscriberDataChannel(dc *webrtc.DataChannel) {
	if s.mode != ModeDataChannel {
		_ = dc.Close()
		return
	}
	dc.OnMessage(s.onDataChannelMessage)
	dc.OnOpen(func() {
		s.subReady.Store(true)
		s.maybeConnected()
	})
}

func (s *Session) onDataChannelMessage(msg webrtc.DataChannelMessage) {
	if s.mode != ModeDataChannel || msg.IsString || len(msg.Data) == 0 {
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
			s.connectedOnce.Do(func() { close(s.connected) })
		}
	case ModeDataChannel:
		if s.dcOpen() != nil && s.subReady.Load() {
			s.connectedOnce.Do(func() { close(s.connected) })
		}
	}
}

func (s *Session) onSubscriberState(state webrtc.PeerConnectionState) {
	s.recordEvidence(Evidence{Stage: "CONNECTION_STATE", Target: "SUBSCRIBER", State: state.String()})
	switch state {
	case webrtc.PeerConnectionStateConnected:
		s.recordEvidence(Evidence{Stage: "SUBSCRIBER_CONNECTED"})
		s.subReady.Store(true)
		s.maybeConnected()
	case webrtc.PeerConnectionStateDisconnected,
		webrtc.PeerConnectionStateFailed,
		webrtc.PeerConnectionStateClosed:
		s.subReady.Store(false)
		if !s.closed.Load() {
			s.disconnects.Add(1)
			s.signalClosed(errors.New("telemost: subscriber disconnected"))
		}
	}
}

func (s *Session) onPublisherState(state webrtc.PeerConnectionState) {
	s.recordEvidence(Evidence{Stage: "CONNECTION_STATE", Target: "PUBLISHER", State: state.String()})
	switch state {
	case webrtc.PeerConnectionStateConnected:
		s.recordEvidence(Evidence{Stage: "PUBLISHER_CONNECTED"})
		s.pubReady.Store(true)
		s.maybeConnected()
	case webrtc.PeerConnectionStateDisconnected,
		webrtc.PeerConnectionStateFailed,
		webrtc.PeerConnectionStateClosed:
		s.pubReady.Store(false)
		if !s.closed.Load() {
			s.disconnects.Add(1)
			s.signalClosed(errors.New("telemost: publisher disconnected"))
		}
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
