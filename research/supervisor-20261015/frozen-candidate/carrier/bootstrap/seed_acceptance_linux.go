//go:build seedacceptance && linux

package bootstrap

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/telemost"
	"golang.org/x/sys/unix"
)

const acceptanceCommand = "CLOSE_CURRENT_SEED_SIGNALING_1011"
const acceptanceMessageLimit = 2048

var acceptanceRejected = errors.New("seed_acceptance_rejected")

type acceptanceContextKey struct{}

type SeedAcceptanceConfig struct {
	Schema       int       `json:"schema"`
	Enabled      bool      `json:"enabled"`
	BinarySHA256 string    `json:"binary_sha256"`
	Directory    string    `json:"directory"`
	ExpiresAt    time.Time `json:"expires_at"`
}

type SeedAcceptanceBinding struct {
	BinarySHA256 string `json:"binary_sha256"`
	PID          int    `json:"pid"`
	StartTicks   uint64 `json:"start_ticks"`
	InvocationID string `json:"invocation_id"`
	Generation   uint64 `json:"generation"`
	RoomHash     string `json:"room_hash"`
}

type SeedAcceptanceCommand struct {
	Schema    int                   `json:"schema"`
	Command   string                `json:"command"`
	Binding   SeedAcceptanceBinding `json:"binding"`
	Nonce     string                `json:"nonce"`
	ArmedAt   time.Time             `json:"armed_at"`
	ExpiresAt time.Time             `json:"expires_at"`
}

type acceptanceTarget struct {
	generation uint64
	active     func() *telemost.Session
}

type seedAcceptance struct {
	mu         sync.Mutex
	binding    SeedAcceptanceBinding
	target     *acceptanceTarget
	consumed   bool
	applied    bool
	created    time.Time
	expires    time.Time
	listener   *net.UnixListener
	queue      chan SeedAcceptanceReceipt
	writerDone chan struct{}
	done       chan struct{}
	ctx        context.Context
	cancel     context.CancelFunc
	selected   *telemost.Session
	nonceHash  string
	closed     bool
	outcome    chan string
}

func acceptanceSeedContext(ctx context.Context, roomID string) context.Context {
	if control, ok := ctx.Value(acceptanceContextKey{}).(*seedAcceptance); ok && control.ctx.Err() == nil {
		return telemost.WithResearchSeedBoundary(ctx, acceptanceHash([]byte(roomID)))
	}
	return ctx
}

func (manager *SeedManager) acceptanceGeneration(generation *seedGeneration) {
	if generation == nil {
		return
	}
	control, ok := generation.ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
	if !ok {
		return
	}
	control.mu.Lock()
	defer control.mu.Unlock()
	if control.closed || control.ctx.Err() != nil {
		return
	}
	control.target = &acceptanceTarget{generation: generation.id, active: func() *telemost.Session {
		manager.mu.Lock()
		defer manager.mu.Unlock()
		if manager.current != generation || generation.ctx.Err() != nil || manager.directory == nil {
			return nil
		}
		observed, ok := generation.carrier.(*observedSeed)
		if !ok {
			return nil
		}
		session, ok := observed.PacketEndpoint.(*telemost.Session)
		if !ok || session.SignalingReadFailure().Kind != "" {
			return nil
		}
		stats := session.Stats()
		if stats.SubscriberState != "connected" || stats.PublisherState != "connected" {
			return nil
		}
		return session
	}}
	if observed, ok := generation.carrier.(*observedSeed); ok {
		if session, ok := observed.PacketEndpoint.(*telemost.Session); ok {
			if control.consumed && control.binding.Generation != generation.id && control.binding.RoomHash == session.ResearchRoomHash() {
				select {
				case control.outcome <- "RECOVERED":
				default:
				}
			} else if !control.consumed {
				binding := control.binding
				binding.Generation = generation.id
				binding.RoomHash = session.ResearchRoomHash()
				select {
				case control.queue <- SeedAcceptanceReceipt{Schema: 1, UTC: time.Now().UTC(), Binding: binding, State: "TARGET_AVAILABLE", PreTriggerSeedState: "ACTIVE", RecoveryOutcome: "NOT_TRIGGERED", CleanupOutcome: "PENDING"}:
				default:
				}
			}
		}
	}
}

func strictAcceptanceJSON(raw []byte, value any) error {
	if len(raw) > acceptanceMessageLimit {
		return acceptanceRejected
	}
	if uniqueAcceptanceKeys(json.NewDecoder(bytes.NewReader(raw)), 0) != nil {
		return acceptanceRejected
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(value) != nil {
		return acceptanceRejected
	}
	var extra any
	if decoder.Decode(&extra) != io.EOF {
		return acceptanceRejected
	}
	return nil
}

func uniqueAcceptanceKeys(decoder *json.Decoder, depth int) error {
	if depth > 4 {
		return acceptanceRejected
	}
	token, err := decoder.Token()
	if err != nil {
		return err
	}
	if delimiter, ok := token.(json.Delim); ok {
		if delimiter != '{' {
			return acceptanceRejected
		}
		seen := map[string]bool{}
		for decoder.More() {
			key, err := decoder.Token()
			if err != nil {
				return err
			}
			name, ok := key.(string)
			if !ok || seen[name] || name != strings.ToLower(name) {
				return acceptanceRejected
			}
			seen[name] = true
			if err := uniqueAcceptanceKeys(decoder, depth+1); err != nil {
				return err
			}
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim('}') {
			return acceptanceRejected
		}
	}
	return nil
}

func trustedAcceptanceParents(path string, serviceUID uint32) bool {
	for directory := filepath.Dir(path); ; directory = filepath.Dir(directory) {
		var stat unix.Stat_t
		if unix.Lstat(directory, &stat) != nil || stat.Mode&unix.S_IFMT != unix.S_IFDIR || stat.Mode&0022 != 0 || (stat.Uid != 0 && stat.Uid != serviceUID) {
			return false
		}
		if directory == "/" {
			return true
		}
	}
}

func acceptanceHash(raw []byte) string {
	digest := sha256.Sum256(raw)
	return hex.EncodeToString(digest[:])
}

func acceptanceProcessBinding() (SeedAcceptanceBinding, error) {
	binary, err := os.Open("/proc/self/exe")
	if err != nil {
		return SeedAcceptanceBinding{}, err
	}
	defer binary.Close()
	digest := sha256.New()
	if _, err = io.Copy(digest, binary); err != nil {
		return SeedAcceptanceBinding{}, err
	}
	raw, err := os.ReadFile("/proc/self/stat")
	if err != nil {
		return SeedAcceptanceBinding{}, err
	}
	end := strings.LastIndex(string(raw), ")")
	if end < 0 {
		return SeedAcceptanceBinding{}, acceptanceRejected
	}
	fields := strings.Fields(string(raw[end+1:]))
	if len(fields) < 20 {
		return SeedAcceptanceBinding{}, acceptanceRejected
	}
	ticks, err := strconv.ParseUint(fields[19], 10, 64)
	if err != nil {
		return SeedAcceptanceBinding{}, err
	}
	invocation := os.Getenv("INVOCATION_ID")
	if invocation != "" {
		if len(invocation) != 32 {
			return SeedAcceptanceBinding{}, acceptanceRejected
		}
		if _, err = hex.DecodeString(invocation); err != nil {
			return SeedAcceptanceBinding{}, acceptanceRejected
		}
	}
	return SeedAcceptanceBinding{BinarySHA256: hex.EncodeToString(digest.Sum(nil)), PID: os.Getpid(), StartTicks: ticks, InvocationID: invocation}, nil
}

func readAcceptanceConfig(path string) (SeedAcceptanceConfig, error) {
	var config SeedAcceptanceConfig
	if !filepath.IsAbs(path) {
		return config, acceptanceRejected
	}
	if !trustedAcceptanceParents(path, 0) {
		return config, acceptanceRejected
	}
	var parent unix.Stat_t
	if unix.Lstat(filepath.Dir(path), &parent) != nil || parent.Mode&unix.S_IFMT != unix.S_IFDIR || parent.Uid != 0 || parent.Mode&0022 != 0 {
		return config, acceptanceRejected
	}
	descriptor, err := unix.Open(path, unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
	if err != nil {
		return config, acceptanceRejected
	}
	file := os.NewFile(uintptr(descriptor), path)
	defer file.Close()
	var stat unix.Stat_t
	if unix.Fstat(descriptor, &stat) != nil || stat.Uid != 0 || stat.Mode&unix.S_IFMT != unix.S_IFREG || (stat.Mode&0777 != 0600 && stat.Mode&0777 != 0640) {
		return config, acceptanceRejected
	}
	raw, err := io.ReadAll(io.LimitReader(file, acceptanceMessageLimit+1))
	if err != nil || strictAcceptanceJSON(raw, &config) != nil {
		return config, acceptanceRejected
	}
	return config, nil
}

func StartSeedAcceptance(ctx context.Context, configPath string) (context.Context, func(), error) {
	if configPath == "" {
		return ctx, func() {}, nil
	}
	config, err := readAcceptanceConfig(configPath)
	if err != nil {
		return ctx, nil, err
	}
	if !trustedAcceptanceParents(filepath.Join(config.Directory, "seed-acceptance.sock"), uint32(os.Geteuid())) {
		return ctx, nil, acceptanceRejected
	}
	binding, err := acceptanceProcessBinding()
	if err != nil {
		return ctx, nil, acceptanceRejected
	}
	return startSeedAcceptance(ctx, config, binding, 0)
}

func startSeedAcceptance(parent context.Context, config SeedAcceptanceConfig, binding SeedAcceptanceBinding, peerUID uint32) (context.Context, func(), error) {
	now := time.Now()
	if config.Schema != 1 || !config.Enabled || config.BinarySHA256 != binding.BinarySHA256 || !config.ExpiresAt.After(now) || config.ExpiresAt.After(now.Add(25*time.Minute)) || !filepath.IsAbs(config.Directory) {
		return parent, nil, acceptanceRejected
	}
	var stat unix.Stat_t
	if unix.Lstat(config.Directory, &stat) != nil || stat.Mode&unix.S_IFMT != unix.S_IFDIR || stat.Mode&0777 != 0700 || stat.Uid != uint32(os.Geteuid()) {
		return parent, nil, acceptanceRejected
	}
	listener, err := net.ListenUnix("unix", &net.UnixAddr{Name: filepath.Join(config.Directory, "seed-acceptance.sock"), Net: "unix"})
	if err != nil {
		return parent, nil, acceptanceRejected
	}
	listener.SetUnlinkOnClose(true)
	if os.Chmod(listener.Addr().String(), 0600) != nil {
		listener.Close()
		return parent, nil, acceptanceRejected
	}
	ctx, cancel := context.WithDeadline(parent, config.ExpiresAt)
	control := &seedAcceptance{binding: binding, created: now, expires: config.ExpiresAt, listener: listener, queue: make(chan SeedAcceptanceReceipt, 32), writerDone: make(chan struct{}), done: make(chan struct{}), ctx: ctx, cancel: cancel, outcome: make(chan string, 1)}
	go control.writeReceipts(config.Directory)
	control.emit("DISABLED", false, "NOT_TRIGGERED", "PENDING")
	stop := context.AfterFunc(ctx, func() { listener.Close() })
	go func() {
		defer close(control.done)
		defer func() {
			control.mu.Lock()
			control.closed = true
			control.selected = nil
			control.target = nil
			close(control.queue)
			control.mu.Unlock()
		}()
		defer stop()
		defer cancel()
		for {
			connection, err := listener.AcceptUnix()
			if err != nil {
				break
			}
			control.handle(connection, peerUID)
			connection.Close()
		}
		control.mu.Lock()
		consumed := control.consumed
		applied := control.applied
		control.mu.Unlock()
		if !consumed {
			control.emit("EXPIRED", false, "NOT_TRIGGERED", "PENDING")
		}
		outcome := "NOT_TRIGGERED"
		if consumed {
			timer := time.NewTimer(ConnectTimeout + 5*time.Second)
			select {
			case outcome = <-control.outcome:
			case <-timer.C:
				outcome = "NOT_OBSERVED_WITHIN_BUDGET"
			case <-ctx.Done():
				outcome = "SERVICE_STOP_OR_CONTROL_EXPIRY"
			}
			timer.Stop()
		}
		_, err := os.Lstat(listener.Addr().String())
		cleanup := "FAILED"
		if os.IsNotExist(err) {
			cleanup = "REMOVED"
		}
		control.emit("CLEANED", applied, outcome, cleanup)
	}()
	return context.WithValue(parent, acceptanceContextKey{}, control), func() { cancel(); <-control.done; <-control.writerDone }, nil
}

func (control *seedAcceptance) emit(state string, applied bool, recovery, cleanup string) {
	control.mu.Lock()
	defer control.mu.Unlock()
	if control.closed {
		return
	}
	receipt := SeedAcceptanceReceipt{Schema: 1, UTC: time.Now().UTC(), Binding: control.binding, NonceHash: control.nonceHash, State: state, ActionApplied: applied, RecoveryOutcome: recovery, CleanupOutcome: cleanup, TestTriggered: applied}
	receipt.PreTriggerSeedState = "NOT_TARGETED"
	if control.selected != nil {
		receipt.PreTriggerSeedState = "ACTIVE"
		receipt.ReaderObserved1011 = control.selected.ResearchTriggerObserved()
	}
	select {
	case control.queue <- receipt:
	default:
	}
}

func (control *seedAcceptance) handle(connection *net.UnixConn, peerUID uint32) {
	connection.SetDeadline(time.Now().Add(time.Second))
	authorized := false
	raw, err := connection.SyscallConn()
	if err == nil {
		err = raw.Control(func(descriptor uintptr) {
			credentials, failure := unix.GetsockoptUcred(int(descriptor), unix.SOL_SOCKET, unix.SO_PEERCRED)
			authorized = failure == nil && credentials.Uid == peerUID
		})
	}
	if err != nil || !authorized {
		io.WriteString(connection, "REJECTED\n")
		return
	}
	request, err := io.ReadAll(io.LimitReader(connection, acceptanceMessageLimit+1))
	var command SeedAcceptanceCommand
	if err != nil || strictAcceptanceJSON(request, &command) != nil || !control.consume(command, time.Now()) {
		io.WriteString(connection, "REJECTED\n")
		return
	}
	io.WriteString(connection, "CONSUMED\n")
	control.listener.Close()
}

func (control *seedAcceptance) consume(command SeedAcceptanceCommand, now time.Time) bool {
	control.mu.Lock()
	if control.consumed || control.ctx.Err() != nil || command.Schema != 1 || command.Command != acceptanceCommand || command.ArmedAt.Before(control.created) || command.ArmedAt.After(now) || !command.ExpiresAt.After(now) || command.ExpiresAt.After(control.expires) || command.ExpiresAt.Sub(command.ArmedAt) > time.Minute || len(command.Nonce) != 64 {
		control.mu.Unlock()
		return false
	}
	if _, err := hex.DecodeString(command.Nonce); err != nil {
		control.mu.Unlock()
		return false
	}
	target := control.target
	expected := control.binding
	control.mu.Unlock()
	if target == nil {
		return false
	}
	session := target.active()
	if session == nil {
		return false
	}
	expected.Generation = target.generation
	expected.RoomHash = session.ResearchRoomHash()
	if command.Binding != expected {
		return false
	}
	control.mu.Lock()
	if control.consumed || control.target != target || control.ctx.Err() != nil {
		control.mu.Unlock()
		return false
	}
	control.consumed = true
	control.binding = expected
	control.selected = session
	control.nonceHash = acceptanceHash([]byte(command.Nonce))
	control.mu.Unlock()
	control.emit("ARMED", false, "PENDING", "PENDING")
	control.emit("READY", false, "PENDING", "PENDING")
	applied := session.ResearchCloseSeed1011()
	control.mu.Lock()
	control.applied = applied
	control.mu.Unlock()
	control.emit("CONSUMED", applied, "SEE_SEED_RECOVERY_RECEIPT", "PENDING")
	return true
}
