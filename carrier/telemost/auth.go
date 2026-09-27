// Package telemost implements a minimal Telemost (Yandex) conference adapter
// for an opaque binary carrier over a real SFU media path.
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
	"time"
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
	RoomID       string `json:"room_id"`
	PeerID       string `json:"peer_id"`
	Credentials  string `json:"credentials"`
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

func validRoom(room string) bool {
	parsed, err := url.Parse(NormalizeRoomURL(room))
	if err != nil || parsed.Scheme != "https" || parsed.Host != "telemost.yandex.ru" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" {
		return false
	}
	identifier := strings.TrimPrefix(parsed.Path, "/j/")
	if identifier == parsed.Path || len(identifier) == 0 || len(identifier) > 128 {
		return false
	}
	for _, character := range identifier {
		if !(character >= '0' && character <= '9' || character >= 'a' && character <= 'z' || character >= 'A' && character <= 'Z' || character == '-' || character == '_') {
			return false
		}
	}
	return true
}

func validSignalingURL(raw string) bool {
	parsed, err := url.Parse(raw)
	if err != nil || parsed.Scheme != "wss" || parsed.User != nil || parsed.Fragment != "" || (parsed.Port() != "" && parsed.Port() != "443") {
		return false
	}
	host := parsed.Hostname()
	for _, suffix := range []string{".yandex.ru", ".yandex.net", ".yandex.com"} {
		if strings.HasSuffix(host, suffix) {
			return true
		}
	}
	return false
}

// FetchConnection retrieves connection metadata for the given room.
func (a *Auth) FetchConnection(ctx context.Context, roomURL, displayName string) (ConnectionInfo, error) {
	var info ConnectionInfo
	full := NormalizeRoomURL(roomURL)
	if !validRoom(roomURL) {
		return info, errors.New("telemost: invalid room URL")
	}
	apiURL := a.APIURL
	if apiURL == "" {
		apiURL = DefaultAPIURL
	}
	client := a.Client
	if client == nil {
		client = &http.Client{Timeout: 15 * time.Second}
	}
	boundedClient := *client
	boundedClient.Timeout = 15 * time.Second
	boundedClient.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }

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

	resp, err := boundedClient.Do(req)
	if err != nil {
		return info, errors.New("telemost: HTTP connection failed")
	}
	defer func() { _ = resp.Body.Close() }()

	if resp.StatusCode != http.StatusOK {
		return info, fmt.Errorf("%w: HTTP status %d", ErrAPI, resp.StatusCode)
	}
	dec := json.NewDecoder(io.LimitReader(resp.Body, 8<<20))
	if err := dec.Decode(&info); err != nil {
		return info, errors.New("telemost: invalid connection response")
	}
	if info.RoomID == "" || info.PeerID == "" || info.Credentials == "" || !validSignalingURL(info.ClientConfig.MediaServerURL) {
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
