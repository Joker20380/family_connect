package telemost

import (
	"fmt"
	"net/http"
	"runtime"
	"strings"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/rtp"
	"github.com/pion/webrtc/v4"
	"github.com/pion/webrtc/v4/pkg/media"
)

func (s *Session) dialWebSocket() error {
	dialer := websocket.Dialer{
		HandshakeTimeout: wsHandshakeTimeout,
		Proxy:            http.ProxyFromEnvironment,
	}
	header := http.Header{}
	header.Set("Origin", DefaultOrigin)
	conn, resp, err := dialer.Dial(s.wsURL, header)
	if err != nil {
		return fmt.Errorf("telemost: dial signaling: %w", err)
	}
	if resp != nil && resp.Body != nil {
		_ = resp.Body.Close()
	}
	conn.SetReadLimit(wsReadLimit)
	conn.SetPongHandler(func(string) error {
		_ = conn.SetReadDeadline(time.Now().Add(wsReadTimeout))
		return nil
	})
	_ = conn.SetReadDeadline(time.Now().Add(wsReadTimeout))
	s.wsMu.Lock()
	s.ws = conn
	s.wsMu.Unlock()
	return nil
}

func (s *Session) writeJSON(v any) error {
	s.wsMu.Lock()
	defer s.wsMu.Unlock()
	if s.ws == nil {
		return errorsTelemost("signaling websocket closed")
	}
	_ = s.ws.SetWriteDeadline(time.Now().Add(wsWriteTimeout))
	if err := s.ws.WriteJSON(v); err != nil {
		return fmt.Errorf("telemost: ws write: %w", err)
	}
	return nil
}

func errorsTelemost(msg string) error { return fmt.Errorf("telemost: %s", msg) }

func (s *Session) sendHello() error {
	sendVideo := s.mode == ModeVP8
	hello := map[string]any{
		"uid": newUUID(),
		"hello": map[string]any{
			"participantMeta": map[string]any{
				"name":        s.cfg.DisplayName,
				"role":        "SPEAKER",
				"description": "",
				"sendAudio":   false,
				"sendVideo":   sendVideo,
			},
			"participantAttributes": map[string]any{
				"name":        s.cfg.DisplayName,
				"role":        "SPEAKER",
				"description": "",
			},
			"sendAudio":         false,
			"sendVideo":         sendVideo,
			"sendSharing":       false,
			"participantId":     s.peerID,
			"roomId":            s.roomID,
			"serviceName":       "telemost",
			"credentials":       s.credentials,
			"capabilitiesOffer": capabilitiesOffer(),
			"sdkInfo": map[string]any{
				"implementation": "browser",
				"version":        "5.27.0",
				"userAgent":      s.auth.UserAgent,
				"hwConcurrency":  runtime.NumCPU(),
			},
			"sdkInitializationId": newUUID(),
			// Both carriers need the publisher peer connection, so never
			// advertise disablePublisher.
			"disablePublisher":       false,
			"disableSubscriber":      false,
			"disableSubscriberAudio": true,
		},
	}
	return s.writeJSON(hello)
}

func (s *Session) signalingLoop() {
	defer s.wg.Done()
	conn := s.wsConn()
	if conn == nil {
		return
	}
	pubOfferSent := false
	for {
		var msg map[string]any
		if err := conn.ReadJSON(&msg); err != nil {
			if !s.closed.Load() {
				s.signalClosed(fmt.Errorf("telemost: signaling read: %w", err))
			}
			return
		}
		_ = conn.SetReadDeadline(time.Now().Add(wsReadTimeout))

		uid, _ := msg["uid"].(string)

		if _, ok := msg["ack"]; ok {
			// no-op: acks are consumed implicitly.
		}
		if serverHello, ok := msg["serverHello"].(map[string]any); ok {
			s.applyServerHello(serverHello)
			s.sendAck(uid)
		}
		if isEndMessage(msg) {
			s.signalClosed(fmt.Errorf("telemost: conference ended"))
			return
		}
		if offer, ok := msg["subscriberSdpOffer"].(map[string]any); ok {
			if err := s.handleSubscriberOffer(offer, uid, !pubOfferSent); err == nil {
				pubOfferSent = true
			}
		}
		if answer, ok := msg["publisherSdpAnswer"].(map[string]any); ok {
			s.handlePublisherAnswer(answer)
			s.sendAck(uid)
		}
		if cand, ok := msg["webrtcIceCandidate"].(map[string]any); ok {
			s.handleRemoteICE(cand)
		}
		s.handleHousekeeping(msg, uid)
	}
}

func (s *Session) wsConn() *websocket.Conn {
	s.wsMu.Lock()
	defer s.wsMu.Unlock()
	return s.ws
}

func (s *Session) signalClosed(err error) {
	s.connectErr = err
	s.closed.Store(true)
	select {
	case <-s.connected:
	default:
		close(s.connected)
	}
	select {
	case <-s.closeCh:
	default:
		close(s.closeCh)
	}
}

func (s *Session) applyServerHello(serverHello map[string]any) {
	rawCfg, ok := serverHello["rtcConfiguration"].(map[string]any)
	if !ok {
		return
	}
	rawServers, ok := rawCfg["iceServers"].([]any)
	if !ok || len(rawServers) == 0 {
		return
	}
	var servers []webrtc.ICEServer
	for _, raw := range rawServers {
		sv, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		var urls []string
		switch u := sv["urls"].(type) {
		case []any:
			for _, x := range u {
				if str, ok := x.(string); ok {
					urls = append(urls, str)
				}
			}
		case string:
			urls = []string{u}
		}
		if len(urls) == 0 {
			continue
		}
		ice := webrtc.ICEServer{URLs: urls}
		if user, ok := sv["username"].(string); ok {
			ice.Username = user
		}
		if cred, ok := sv["credential"].(string); ok {
			ice.Credential = cred
		}
		servers = append(servers, ice)
	}
	if len(servers) == 0 {
		return
	}
	cfg := webrtc.Configuration{
		ICEServers:   servers,
		SDPSemantics: webrtc.SDPSemanticsUnifiedPlan,
	}
	if sub := s.pcSub.Load(); sub != nil {
		_ = sub.SetConfiguration(cfg)
	}
	if pub := s.pcPub.Load(); pub != nil {
		_ = pub.SetConfiguration(cfg)
	}
}

func (s *Session) handleSubscriberOffer(offer map[string]any, uid string, sendPub bool) error {
	sub := s.pcSub.Load()
	if sub == nil {
		return errorsTelemost("subscriber pc missing")
	}
	sdp, _ := offer["sdp"].(string)
	if sdp == "" {
		return errorsTelemost("empty subscriber offer")
	}
	if err := sub.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeOffer, SDP: sdp}); err != nil {
		return fmt.Errorf("telemost: set subscriber remote: %w", err)
	}
	answer, err := sub.CreateAnswer(nil)
	if err != nil {
		return fmt.Errorf("telemost: create subscriber answer: %w", err)
	}
	if err := sub.SetLocalDescription(answer); err != nil {
		return fmt.Errorf("telemost: set subscriber local: %w", err)
	}
	if err := s.writeJSON(map[string]any{
		"uid": newUUID(),
		"subscriberSdpAnswer": map[string]any{
			"pcSeq": 1,
			"sdp":   answer.SDP,
		},
	}); err != nil {
		return err
	}
	s.sendAck(uid)

	if s.mode == ModeVP8 {
		s.sendSetSlots()
	}

	if !sendPub {
		return nil
	}

	// Give the SFU time to apply the subscriber answer before the publisher
	// offer lands on the same channel; SEPARATE offer/answer mode drops an
	// early publisher offer.
	time.Sleep(300 * time.Millisecond)
	return s.sendPublisherOffer()
}

func (s *Session) sendPublisherOffer() error {
	pub := s.pcPub.Load()
	if pub == nil {
		return errorsTelemost("publisher pc missing")
	}
	offer, err := pub.CreateOffer(nil)
	if err != nil {
		return fmt.Errorf("telemost: create publisher offer: %w", err)
	}
	if err := pub.SetLocalDescription(offer); err != nil {
		return fmt.Errorf("telemost: set publisher local: %w", err)
	}
	return s.writeJSON(map[string]any{
		"uid": newUUID(),
		"publisherSdpOffer": map[string]any{
			"pcSeq":  1,
			"sdp":    offer.SDP,
			"tracks": s.publisherTrackDescriptions(),
		},
	})
}

func (s *Session) handlePublisherAnswer(answer map[string]any) {
	pub := s.pcPub.Load()
	if pub == nil {
		return
	}
	sdp, _ := answer["sdp"].(string)
	if sdp == "" {
		return
	}
	_ = pub.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeAnswer, SDP: sdp})
}

func (s *Session) publisherTrackDescriptions() []map[string]any {
	pub := s.pcPub.Load()
	if pub == nil {
		return []map[string]any{}
	}
	tracks := make([]map[string]any, 0)
	for _, tr := range pub.GetTransceivers() {
		sender := tr.Sender()
		if sender == nil || sender.Track() == nil {
			continue
		}
		kind := "VIDEO"
		if sender.Track().Kind() == webrtc.RTPCodecTypeAudio {
			kind = "AUDIO"
		}
		tracks = append(tracks, map[string]any{
			"mid":            tr.Mid(),
			"transceiverMid": tr.Mid(),
			"kind":           kind,
			"priority":       0,
			"label":          sender.Track().ID(),
			"codecs":         map[string]any{},
			"groupId":        1,
			"description":    "",
		})
	}
	return tracks
}

func (s *Session) sendSetSlots() {
	slots := make([]map[string]int, 0, 8)
	for range 8 {
		slots = append(slots, map[string]int{"width": 1280, "height": 720})
	}
	_ = s.writeJSON(map[string]any{
		"uid": newUUID(),
		"setSlots": map[string]any{
			"slots":              slots,
			"audioSlotsCount":    0,
			"key":                1,
			"shutdownAllVideo":   nil,
			"withSelfView":       false,
			"selfViewVisibility": "ON_LOADING_THEN_SHOW",
			"gridConfig":         map[string]any{},
		},
	})
}

func (s *Session) setupICEHandlers() {
	if sub := s.pcSub.Load(); sub != nil {
		sub.OnICECandidate(s.iceHandler("SUBSCRIBER"))
	}
	if pub := s.pcPub.Load(); pub != nil {
		pub.OnICECandidate(s.iceHandler("PUBLISHER"))
	}
}

func (s *Session) iceHandler(target string) func(*webrtc.ICECandidate) {
	return func(c *webrtc.ICECandidate) {
		if c == nil {
			return
		}
		init := c.ToJSON()
		_ = s.writeJSON(map[string]any{
			"uid": newUUID(),
			"webrtcIceCandidate": map[string]any{
				"candidate":     init.Candidate,
				"sdpMid":        init.SDPMid,
				"sdpMlineIndex": init.SDPMLineIndex,
				"target":        target,
				"pcSeq":         1,
			},
		})
	}
}

func (s *Session) handleRemoteICE(cand map[string]any) {
	candidate, _ := cand["candidate"].(string)
	target, _ := cand["target"].(string)
	sdpMid, _ := cand["sdpMid"].(string)
	idx, _ := cand["sdpMlineIndex"].(float64)
	if candidate == "" || len(strings.Fields(candidate)) < 8 {
		return
	}
	mlIndex := uint16(idx)
	init := webrtc.ICECandidateInit{
		Candidate:     candidate,
		SDPMid:        &sdpMid,
		SDPMLineIndex: &mlIndex,
	}
	switch target {
	case "SUBSCRIBER":
		if sub := s.pcSub.Load(); sub != nil {
			_ = sub.AddICECandidate(init)
		}
	case "PUBLISHER":
		if pub := s.pcPub.Load(); pub != nil {
			_ = pub.AddICECandidate(init)
		}
	}
}

func (s *Session) sendAck(uid string) {
	if uid == "" {
		return
	}
	_ = s.writeJSON(map[string]any{
		"uid": uid,
		"ack": map[string]any{
			"status": map[string]any{"code": "OK"},
		},
	})
}

func (s *Session) handleHousekeeping(msg map[string]any, uid string) {
	switch {
	case hasKey(msg, "ping"):
		_ = s.writeJSON(map[string]any{"uid": uid, "pong": map[string]any{}})
	case hasKey(msg, "updateDescription"),
		hasKey(msg, "upsertDescription"),
		hasKey(msg, "removeDescription"),
		hasKey(msg, "slotsConfig"),
		hasKey(msg, "slotsMeta"),
		hasKey(msg, "vadActivity"):
		s.sendAck(uid)
	}
}

func hasKey(m map[string]any, k string) bool {
	_, ok := m[k]
	return ok
}

func isEndMessage(msg map[string]any) bool {
	for _, k := range []string{"conferenceClosed", "conferenceEnded", "roomClosed", "roomEnded", "callEnded"} {
		if hasKey(msg, k) {
			return true
		}
	}
	if raw, ok := msg["conference"].(map[string]any); ok {
		if st, _ := raw["state"].(string); isEndedState(st) {
			return true
		}
	}
	if raw, ok := msg["conferenceState"].(map[string]any); ok {
		if st, _ := raw["state"].(string); isEndedState(st) {
			return true
		}
	}
	return false
}

func isEndedState(st string) bool {
	switch strings.ToLower(st) {
	case "closed", "ended", "finished", "terminated":
		return true
	default:
		return false
	}
}

// writerLoop drains the send queue into the active transport. For VP8 it also
// injects a decodable keepalive keyframe so the SFU keeps forwarding the track.
func (s *Session) writerLoop() {
	defer s.wg.Done()
	if s.mode == ModeVP8 {
		keepalive := time.NewTicker(vp8KeepaliveInterval)
		defer keepalive.Stop()
		for {
			select {
			case <-s.closeCh:
				return
			case <-keepalive.C:
				s.writeVP8Sample(vp8Keepalive)
			case frame, ok := <-s.sendQueue:
				if !ok {
					return
				}
				s.writeVP8Sample(frame)
				time.Sleep(vp8SendInterval)
			}
		}
	}

	for {
		select {
		case <-s.closeCh:
			return
		case frame, ok := <-s.sendQueue:
			if !ok {
				return
			}
			if !s.writeDCMessage(frame) {
				return
			}
		}
	}
}

func (s *Session) writeVP8Sample(data []byte) {
	if s.track == nil {
		return
	}
	_ = s.track.WriteSample(media.Sample{Data: data, Duration: vp8FrameDuration})
}

func (s *Session) writeDCMessage(data []byte) bool {
	dc := s.dc.Load()
	if dc == nil || dc.ReadyState() != webrtc.DataChannelStateOpen {
		return false
	}
	for dc.BufferedAmount() > dcBufferedHighWaterMark {
		select {
		case <-s.closeCh:
			return false
		case <-time.After(5 * time.Millisecond):
		}
	}
	return dc.Send(data) == nil
}

// capabilitiesOffer is the Telemost feature matrix advertised in hello.
func capabilitiesOffer() map[string]any {
	return map[string]any{
		"offerAnswerMode":           []string{"SEPARATE"},
		"initialSubscriberOffer":    []string{"ON_HELLO"},
		"slotsMode":                 []string{"FROM_CONTROLLER"},
		"simulcastMode":             []string{"DISABLED", "STATIC"},
		"selfVadStatus":             []string{"FROM_SERVER", "FROM_CLIENT"},
		"dataChannelSharing":        []string{"TO_RTP"},
		"videoEncoderConfig":        []string{"NO_CONFIG", "ONLY_INIT_CONFIG", "RUNTIME_CONFIG"},
		"dataChannelVideoCodec":     []string{"VP8", "UNIQUE_CODEC_FROM_TRACK_DESCRIPTION"},
		"bandwidthLimitationReason": []string{"BANDWIDTH_REASON_DISABLED", "BANDWIDTH_REASON_ENABLED"},
		"sdkDefaultDeviceManagement": []string{
			"SDK_DEFAULT_DEVICE_MANAGEMENT_DISABLED",
			"SDK_DEFAULT_DEVICE_MANAGEMENT_ENABLED",
		},
		"joinOrderLayout": []string{"JOIN_ORDER_LAYOUT_DISABLED", "JOIN_ORDER_LAYOUT_ENABLED"},
		"pinLayout":       []string{"PIN_LAYOUT_DISABLED"},
		"sendSelfViewVideoSlot": []string{
			"SEND_SELF_VIEW_VIDEO_SLOT_DISABLED",
			"SEND_SELF_VIEW_VIDEO_SLOT_ENABLED",
		},
		"serverLayoutTransition": []string{"SERVER_LAYOUT_TRANSITION_DISABLED"},
		"sdkPublisherOptimizeBitrate": []string{
			"SDK_PUBLISHER_OPTIMIZE_BITRATE_DISABLED",
			"SDK_PUBLISHER_OPTIMIZE_BITRATE_FULL",
			"SDK_PUBLISHER_OPTIMIZE_BITRATE_ONLY_SELF",
		},
		"sdkNetworkLostDetection":   []string{"SDK_NETWORK_LOST_DETECTION_DISABLED"},
		"sdkNetworkPathMonitor":     []string{"SDK_NETWORK_PATH_MONITOR_DISABLED"},
		"publisherVp9":              []string{"PUBLISH_VP9_DISABLED", "PUBLISH_VP9_ENABLED"},
		"svcMode":                   []string{"SVC_MODE_DISABLED", "SVC_MODE_L3T3", "SVC_MODE_L3T3_KEY"},
		"subscriberOfferAsyncAck":   []string{"SUBSCRIBER_OFFER_ASYNC_ACK_DISABLED", "SUBSCRIBER_OFFER_ASYNC_ACK_ENABLED"},
		"androidBluetoothRoutingFix": []string{"ANDROID_BLUETOOTH_ROUTING_FIX_DISABLED"},
		"fixedIceCandidatesPoolSize": []string{"FIXED_ICE_CANDIDATES_POOL_SIZE_DISABLED"},
		"sdkAndroidTelecomIntegration": []string{"SDK_ANDROID_TELECOM_INTEGRATION_DISABLED"},
		"setActiveCodecsMode": []string{"SET_ACTIVE_CODECS_MODE_DISABLED", "SET_ACTIVE_CODECS_MODE_VIDEO_ONLY"},
		"subscriberDtlsPassiveMode": []string{"SUBSCRIBER_DTLS_PASSIVE_MODE_DISABLED"},
		"publisherOpusDred":         []string{"PUBLISHER_OPUS_DRED_DISABLED"},
		"publisherOpusLowBitrate":   []string{"PUBLISHER_OPUS_LOW_BITRATE_DISABLED"},
		"sdkAndroidDestroySessionOnTaskRemoved": []string{
			"SDK_ANDROID_DESTROY_SESSION_ON_TASK_REMOVED_DISABLED",
		},
		"svcModes":                []string{"FALSE"},
		"reportTelemetryModes":    []string{"TRUE"},
		"keepDefaultDevicesModes": []string{"FALSE"},
	}
}

// readVP8Track consumes an incoming VP8 track, reassembles RTP into VP8 frames
// and feeds carried fragments to the reassembler.
func (s *Session) readVP8Track(track *webrtc.TrackRemote) {
	var state vp8FrameState
	reorder := newReorderBuffer()
	buf := make([]byte, 65536)
	for {
		n, _, err := track.Read(buf)
		if err != nil {
			return
		}
		pkt := &rtp.Packet{}
		if pkt.Unmarshal(buf[:n]) != nil {
			continue
		}
		reorder.push(pkt, func(ordered *rtp.Packet) {
			frame := state.process(ordered)
			if frame == nil {
				return
			}
			if frag, ok := decodeVP8Frame(frame); ok {
				s.reassembler.ingest(frag)
			}
		})
	}
}
