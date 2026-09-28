package roombroker

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
	"time"
)

const ConferenceEndpoint = "https://cloud-api.yandex.net/v1/telemost-api/conferences"
const CreationTimeout = 15 * time.Second
const maxResponse = 16 << 10

type Code string

func (code Code) Error() string { return "room broker: " + string(code) }

type Room struct {
	ID      string
	JoinURL string
}

func (Room) String() string   { return "[ephemeral room redacted]" }
func (Room) GoString() string { return "[ephemeral room redacted]" }

type RoomProvider interface {
	CreateRoom(context.Context) (Room, error)
}

type TelemostRoomProvider struct {
	token    string
	client   *http.Client
	endpoint string
}

func (*TelemostRoomProvider) String() string   { return "[Telemost provider redacted]" }
func (*TelemostRoomProvider) GoString() string { return "[Telemost provider redacted]" }

func NewTelemostRoomProvider() (*TelemostRoomProvider, error) {
	token := os.Getenv("YANDEX_TELEMOST_OAUTH_TOKEN")
	if token == "" || len(token) > 4096 || strings.ContainsAny(token, "\r\n\x00") {
		return nil, Code("provider_credentials_unavailable")
	}
	return &TelemostRoomProvider{token: token, endpoint: ConferenceEndpoint, client: &http.Client{
		Timeout:       CreationTimeout,
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}}, nil
}

var roomPath = regexp.MustCompile(`^/j/[A-Za-z0-9_-]{1,128}$`)

func ValidJoinURL(value string) bool {
	parsed, err := url.Parse(value)
	return err == nil && len(value) <= 2048 && parsed.Scheme == "https" && parsed.Host == "telemost.yandex.ru" &&
		parsed.User == nil && parsed.RawQuery == "" && !parsed.ForceQuery && parsed.Fragment == "" &&
		parsed.RawPath == "" && roomPath.MatchString(parsed.Path)
}

func (provider *TelemostRoomProvider) CreateRoom(ctx context.Context) (Room, error) {
	ctx, cancel := context.WithTimeout(ctx, CreationTimeout)
	defer cancel()
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, provider.endpoint,
		strings.NewReader(`{"waiting_room_level":"PUBLIC"}`))
	if err != nil {
		return Room{}, Code("provider_request")
	}
	request.Header.Set("Authorization", "OAuth "+provider.token)
	request.Header.Set("Content-Type", "application/json")
	response, err := provider.client.Do(request)
	if err != nil {
		if errors.Is(ctx.Err(), context.Canceled) {
			return Room{}, Code("provider_cancelled")
		}
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return Room{}, Code("provider_timeout")
		}
		var timeout interface{ Timeout() bool }
		if errors.As(err, &timeout) && timeout.Timeout() {
			return Room{}, Code("provider_timeout")
		}
		return Room{}, Code("provider_transport")
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusCreated {
		switch response.StatusCode {
		case 400:
			return Room{}, Code("provider_bad_request")
		case 401:
			return Room{}, Code("provider_unauthorized")
		case 403:
			return Room{}, Code("provider_forbidden")
		case 429:
			return Room{}, Code("provider_rate_limited")
		}
		if response.StatusCode >= 500 {
			return Room{}, Code("provider_unavailable")
		}
		return Room{}, Code("provider_status")
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, maxResponse+1))
	if ctx.Err() != nil {
		if errors.Is(ctx.Err(), context.Canceled) {
			return Room{}, Code("provider_cancelled")
		}
		return Room{}, Code("provider_timeout")
	}
	if err != nil || len(raw) > maxResponse {
		return Room{}, Code("provider_body")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	start, err := decoder.Token()
	if err != nil || start != json.Delim('{') {
		return Room{}, Code("provider_json")
	}
	fields := make(map[string]json.RawMessage)
	for decoder.More() {
		key, err := decoder.Token()
		if err != nil {
			return Room{}, Code("provider_json")
		}
		name, ok := key.(string)
		if !ok || fields[name] != nil {
			return Room{}, Code("provider_json")
		}
		var value json.RawMessage
		if decoder.Decode(&value) != nil {
			return Room{}, Code("provider_json")
		}
		fields[name] = value
	}
	if _, err := decoder.Token(); err != nil || decoder.Decode(new(any)) != io.EOF {
		return Room{}, Code("provider_json")
	}
	var room Room
	if json.Unmarshal(fields["id"], &room.ID) != nil || len(room.ID) == 0 || len(room.ID) > 256 || strings.TrimSpace(room.ID) != room.ID {
		return Room{}, Code("provider_id")
	}
	for _, char := range room.ID {
		if char < 33 || char > 126 {
			return Room{}, Code("provider_id")
		}
	}
	if json.Unmarshal(fields["join_url"], &room.JoinURL) != nil || !ValidJoinURL(room.JoinURL) {
		return Room{}, Code("provider_join_url")
	}
	return room, nil
}
