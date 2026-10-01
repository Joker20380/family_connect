package bootstrap

import (
	"context"
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type SeedConnector func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error)

type SeedManager struct {
	mu        sync.Mutex
	directory *Directory
	running   bool
	Event     func(string)
	Publish   func(Directory) error
}

func TelemostSeed(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
	carrier, err := telemost.New(lifetime, telemost.Config{RoomURL: room.JoinURL, DisplayName: "Family bootstrap gateway", Mode: telemost.ModeVP8, MaxVideoTracks: 4})
	if err != nil {
		return nil, roombroker.Code("seed_configuration")
	}
	if err := carrier.Connect(ready); err != nil {
		carrier.Close()
		return nil, roombroker.Code("seed_join_failed")
	}
	return carrier, nil
}

func (manager *SeedManager) Run(ctx context.Context, provider roombroker.RoomProvider, connect SeedConnector, family, gateway string, ttl time.Duration, exchange func(context.Context, familysession.PacketEndpoint)) error {
	if provider == nil || connect == nil || exchange == nil || ttl <= 0 || ttl > MaxAge || !hexID(family, 16) || !hexID(gateway, 16) {
		return roombroker.Code("seed_configuration")
	}
	manager.mu.Lock()
	if manager.running {
		manager.mu.Unlock()
		return roombroker.Code("seed_busy")
	}
	manager.running = true
	manager.mu.Unlock()
	defer func() { manager.mu.Lock(); manager.directory = nil; manager.running = false; manager.mu.Unlock() }()
	creation, cancel := context.WithTimeout(ctx, roombroker.CreationTimeout)
	room, err := provider.CreateRoom(creation)
	creationErr := creation.Err()
	cancel()
	if err != nil || creationErr != nil || !roombroker.ValidJoinURL(room.JoinURL) || room.ID == "" {
		return roombroker.Code("seed_creation_failed")
	}
	lifetime, stop := context.WithTimeout(ctx, ttl)
	defer stop()
	ready, cancel := context.WithTimeout(lifetime, ConnectTimeout)
	carrier, err := connect(lifetime, ready, room)
	readyErr := ready.Err()
	cancel()
	if err != nil || readyErr != nil || carrier == nil {
		if carrier != nil {
			carrier.Close()
		}
		return roombroker.Code("seed_not_ready")
	}
	defer carrier.Close()
	now := time.Now().UTC()
	expires, _ := lifetime.Deadline()
	manager.mu.Lock()
	manager.directory = &Directory{1, family, now, expires.UTC(), []Seed{{"telemost-webrtc", room.JoinURL, gateway}}}
	directory := *manager.directory
	manager.mu.Unlock()
	if manager.Publish != nil {
		if err := manager.Publish(directory); err != nil {
			return roombroker.Code("seed_publication_failed")
		}
	}
	if manager.Event != nil {
		manager.Event("bootstrap_seed_ready")
	}
	return ServeCarrier(lifetime, carrier, exchange)
}

func (manager *SeedManager) Handler(path string) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Cache-Control", "no-store")
		writer.Header().Set("Content-Type", "application/json")
		if request.Method != http.MethodGet || request.URL.Path != "/v1/bootstrap/directory" || request.URL.RawQuery != "" || request.ContentLength != 0 {
			writer.WriteHeader(http.StatusBadRequest)
			return
		}
		identity, err := roombroker.RequestAuthorizer(path, request.TLS)(request.Context())
		if err != nil {
			writer.WriteHeader(http.StatusForbidden)
			return
		}
		manager.mu.Lock()
		defer manager.mu.Unlock()
		if manager.directory == nil || manager.directory.Family != identity.Family || !time.Now().Before(manager.directory.ExpiresAt) {
			writer.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		_ = json.NewEncoder(writer).Encode(manager.directory)
	})
}
