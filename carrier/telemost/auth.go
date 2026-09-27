// Package telemost implements a minimal Telemost (Yandex) conference adapter
// for an opaque binary carrier over a real SFU media path.
//
// The protocol facts here were re-derived from the public reference
// implementations audited in docs/legal/DEPENDENCY_LICENSE_AUDIT.md
// (kulikov0/whitelist-bypass @ 7c19a7ec and openlibrecommunity/olcrtc
// @ 92b23327) and are re-implemented, not copied.
package telemost

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
)

const (
	// DefaultAPIURL is the Telemost conference connection REST base.
	DefaultAPIURL = "https://cloud-api.yandex.ru/telemost_front/v2/telemost"
	// DefaultOrigin is the browser Origin used for Telemost API/signaling calls.
	DefaultOrigin = "https://telemost.yandex.ru"
	// roomURLPrefix expands a bare room hash into a full conference URL.
	roomURLPrefix = "https://telemost.yandex.ru/j/"
)

// ErrAPI marks failures returned by the Telemost HTTP API.
var ErrAPI = errors.New("telemost api error")

// ConnectionInfo is the connection metadata returned by the Telemost API.
type ConnectionInfo struct {
	RoomID      string `json:"room_id"`
	PeerID      string `json:"peer_id"`
	Credentials string `json:"credentials"`
	ClientConfig struct {
		MediaServerURL string `json:"media_server_url"`
	} `json:"client_configuration"`
}

// Auth is a self-contained helper that fetches Telemost connection metadata.
type Auth struct {
	APIURL    string
	UserAgent string
	Client    *http.Client
}

// NewAuth returns an Auth with production defaults and the supplied client.
func NewAuth(client *http.Client) *Auth {
	return &Auth{
		APIURL:    DefaultAPIURL,
		UserAgent: "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0",
		Client:    client,
	}
}

// NormalizeRoomURL returns the full conference URL for a room URL or bare hash.
func NormalizeRoomURL(room string) string {
	room = strings.TrimSpace(room)
	if room == "" {
		return ""
	}
	if strings.HasPrefix(room, "http://") || strings.HasPrefix(room, "https://") {
		return room
	}
	return roomURLPrefix + room
}

// FetchConnection retrieves connection metadata for the given room.
func (a *Auth) FetchConnection(ctx context.Context, roomURL, displayName string) (ConnectionInfo, error) {
	var info ConnectionInfo
	full := NormalizeRoomURL(roomURL)
	if full == "" {
		return info, errors.New("telemost: room URL required")
	}
	apiURL := a.APIURL
	if apiURL == "" {
		apiURL = DefaultAPIURL
	}
	client := a.Client
	if client == nil {
		client = http.DefaultClient
	}

	u := fmt.Sprintf("%s/conferences/%s/connection", apiURL, url.QueryEscape(full))
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, http.NoBody)
	if err != nil {
		return info, fmt.Errorf("telemost: build request: %w", err)
	}
	q := req.URL.Query()
	q.Add("next_gen_media_platform_allowed", "true")
	q.Add("display_name", displayName)
	q.Add("waiting_room_supported", "true")
	req.URL.RawQuery = q.Encode()

	ua := a.UserAgent
	if ua == "" {
		ua = "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0"
	}
	req.Header.Set("User-Agent", ua)
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Client-Instance-Id", newUUID())
	req.Header.Set("X-Telemost-Client-Version", "187.1.0")
	req.Header.Set("Idempotency-Key", newUUID())
	req.Header.Set("Origin", DefaultOrigin)
	req.Header.Set("Referer", DefaultOrigin+"/")

	resp, err := client.Do(req)
	if err != nil {
		return info, fmt.Errorf("telemost: do request: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return info, fmt.Errorf("%w: status %d: %s", ErrAPI, resp.StatusCode, redactBody(body))
	}
	dec := json.NewDecoder(io.LimitReader(resp.Body, 8<<20))
	if err := dec.Decode(&info); err != nil {
		return info, fmt.Errorf("telemost: decode response: %w", err)
	}
	if info.RoomID == "" || info.PeerID == "" || info.ClientConfig.MediaServerURL == "" {
		return info, errors.New("telemost: connection response missing required fields")
	}
	return info, nil
}

// newUUID returns a random RFC-4122 version-4 UUID string using crypto/rand so
// the carrier avoids an extra dependency.
func newUUID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		// crypto/rand essentially never fails; fall back to a zero-ish value.
		return "00000000-0000-4000-8000-000000000000"
	}
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant 10
	var dst [36]byte
	hex.Encode(dst[0:8], b[0:4])
	dst[8] = '-'
	hex.Encode(dst[9:13], b[4:6])
	dst[13] = '-'
	hex.Encode(dst[14:18], b[6:8])
	dst[18] = '-'
	hex.Encode(dst[19:23], b[8:10])
	dst[23] = '-'
	hex.Encode(dst[24:36], b[10:16])
	return string(dst[:])
}

// redactBody strips known credential-bearing keys from an error body before it
// is surfaced in a diagnostic.
func redactBody(body []byte) string {
	var m map[string]any
	if err := json.Unmarshal(body, &m); err != nil {
		return "<non-json>"
	}
	redactMap(m)
	out, err := json.Marshal(m)
	if err != nil {
		return "<unmarshalable>"
	}
	return string(out)
}

func redactMap(m map[string]any) {
	for k, v := range m {
		switch strings.ToLower(k) {
		case "credentials", "token", "cookie", "set-cookie", "secret", "authorization":
			m[k] = "[redacted]"
		default:
			if child, ok := v.(map[string]any); ok {
				redactMap(child)
			}
		}
	}
}
