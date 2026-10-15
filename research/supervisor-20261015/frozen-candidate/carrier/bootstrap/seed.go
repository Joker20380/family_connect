package bootstrap

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type SeedConnector func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error)

type SeedFailure struct {
	Stage         string
	Cause         error
	ParentError   error
	Generation    int
	CloseSource   string
	SignalingRead telemost.SignalingReadFailure
}

type SeedManager struct {
	mu            sync.Mutex
	directory     *Directory
	running       bool
	Event         func(string)
	Publish       func(Directory) error
	RotateAfter   time.Duration
	Observe       func(SeedFailure)
	RecoveryCheck func(context.Context) (time.Time, error)
	Recovery      func(SeedRecovery)
	current       *seedGeneration
	now           func() time.Time
	lifetime      func(context.Context, time.Duration) (context.Context, context.CancelFunc)
	after         func(time.Duration, func()) seedTimer
}

func TelemostSeed(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
	lifetime = acceptanceSeedContext(lifetime, room.ID)
	trace := newSeedTrace()
	carrier, err := telemost.New(lifetime, telemost.Config{RoomURL: room.JoinURL, DisplayName: "Family bootstrap gateway", Mode: telemost.ModeVP8, MaxVideoTracks: 4, Trace: trace})
	if err != nil {
		return nil, roombroker.Code("seed_configuration")
	}
	if err := carrier.Connect(ready); err != nil {
		failure := &seedConnectFailure{cause: roombroker.Code("seed_join_failed"), signaling: carrier.SignalingReadFailure()}
		if first := trace.Snapshot().FirstClose; first != nil {
			failure.source = first.CloseSource
		}
		carrier.Close()
		return nil, failure
	}
	return &observedSeed{PacketEndpoint: carrier, trace: trace}, nil
}

type observedSeed struct {
	familysession.PacketEndpoint
	trace *sessiontrace.Recorder
}

func newSeedTrace() *sessiontrace.Recorder {
	identifier := sha256.Sum256([]byte("family-connect/seed-fatal-observation/v1"))
	return sessiontrace.New(hex.EncodeToString(identifier[:]), nil)
}

func (seed *observedSeed) SeedCloseSource() string {
	if first := seed.trace.Snapshot().FirstClose; first != nil {
		return first.CloseSource
	}
	return ""
}

func (seed *observedSeed) SeedSignalingReadFailure() telemost.SignalingReadFailure {
	if source, ok := seed.PacketEndpoint.(interface {
		SignalingReadFailure() telemost.SignalingReadFailure
	}); ok {
		return source.SignalingReadFailure()
	}
	return telemost.SignalingReadFailure{}
}

func (manager *SeedManager) Run(ctx context.Context, provider roombroker.RoomProvider, connect SeedConnector, family, gateway string, ttl time.Duration, exchange func(context.Context, familysession.PacketEndpoint)) error {
	if provider == nil || connect == nil || exchange == nil || ttl <= 0 || ttl > MaxAge || !hexID(family, 16) || !hexID(gateway, 16) {
		return roombroker.Code("seed_configuration")
	}
	if manager.RotateAfter != 0 {
		return manager.runOverlap(ctx, provider, connect, family, gateway, ttl, exchange)
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
		manager.failure("SEED_CREATE", firstError(err, creationErr), ctx.Err())
		return roombroker.Code("seed_creation_failed")
	}
	lifetime, stop := manager.withLifetime(ctx, ttl)
	defer stop()
	generation := newSeedGeneration(lifetime, 1)
	defer func() { generation.close() }()
	ready, cancel := context.WithTimeout(generation.ctx, ConnectTimeout)
	carrier, err := connect(generation.ctx, ready, room)
	generation.carrier = carrier
	readyErr := ready.Err()
	cancel()
	if err != nil || readyErr != nil || carrier == nil {
		manager.failure("SEED_CONNECT", firstError(err, readyErr), ctx.Err())
		if carrier != nil {
			carrier.Close()
		}
		return roombroker.Code("seed_not_ready")
	}
	defer carrier.Close()
	manager.swapGeneration(nil, generation)
	defer func() { manager.swapGeneration(generation, nil) }()
	now := manager.timeNow().UTC()
	expires, _ := lifetime.Deadline()
	manager.mu.Lock()
	manager.directory = &Directory{1, family, now, expires.UTC(), []Seed{{"telemost-webrtc", room.JoinURL, gateway}}}
	directory := *manager.directory
	manager.mu.Unlock()
	if manager.Publish != nil {
		if err := manager.Publish(directory); err != nil {
			manager.failure("DIRECTORY", err, ctx.Err())
			return roombroker.Code("seed_publication_failed")
		}
	}
	if manager.Event != nil {
		manager.Event("bootstrap_seed_ready")
	}
	return manager.supervise(lifetime, room, generation, connect, exchange)
}

func firstError(primary, fallback error) error {
	if primary != nil {
		return primary
	}
	return fallback
}

func (manager *SeedManager) failure(stage string, cause, parent error) {
	if manager.Observe != nil {
		manager.Observe(SeedFailure{Stage: stage, Cause: cause, ParentError: parent})
	}
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
		var directory *Directory
		if manager.directory != nil {
			copy := *manager.directory
			directory = &copy
		}
		manager.mu.Unlock()
		if directory == nil || directory.Family != identity.Family || !manager.timeNow().Before(directory.ExpiresAt) {
			writer.WriteHeader(http.StatusServiceUnavailable)
			return
		}
		_ = json.NewEncoder(writer).Encode(directory)
	})
}
