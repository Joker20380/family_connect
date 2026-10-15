package main

import (
	"context"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"net"
	"os"
	"path/filepath"
	"regexp"
	"runtime/debug"
	"sort"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type fatalRecord struct {
	Schema              int                            `json:"schema"`
	Timestamp           time.Time                      `json:"timestamp_utc"`
	ElapsedMS           int64                          `json:"elapsed_ms"`
	Invocation          string                         `json:"invocation_id"`
	PID                 int                            `json:"pid"`
	Binary              string                         `json:"binary_sha256"`
	Source              string                         `json:"source_sha"`
	ExitPath            string                         `json:"exit_path"`
	LastStage           string                         `json:"last_confirmed_stage"`
	Stage               string                         `json:"first_stage"`
	Cause               string                         `json:"first_cause"`
	ErrorClass          string                         `json:"safe_error_class"`
	SeedCloseSource     string                         `json:"seed_close_source,omitempty"`
	SignalingRead       *telemost.SignalingReadFailure `json:"signaling_read,omitempty"`
	Generation          int                            `json:"seed_generation"`
	Parent              string                         `json:"parent_context_at_failure"`
	Fatal               bool                           `json:"fatal"`
	Signal              string                         `json:"signal"`
	Directory           string                         `json:"directory_sha256"`
	DirectoryGeneration string                         `json:"directory_generation"`
	LimitingExpiry      time.Time                      `json:"credential_limiting_expiry"`
	HeadroomSeconds     int64                          `json:"credential_headroom_seconds"`
	CredentialSnapshot  string                         `json:"credential_snapshot"`
	Lifecycle           string                         `json:"broker_lifecycle"`
	CleanupStarted      bool                           `json:"cleanup_started"`
	CleanupCompleted    bool                           `json:"cleanup_completed"`
}

type fatalObserver struct {
	mu      sync.Mutex
	started time.Time
	dir     string
	sealed  bool
	first   bool
	signals chan os.Signal
	value   fatalRecord
}

var receiptID = regexp.MustCompile(`^[a-f0-9]{32}$`)
var receiptName = regexp.MustCompile(`^application-[a-f0-9]{32}\.json$`)

func newFatalObserver() *fatalObserver {
	observer := &fatalObserver{started: time.Now(), dir: os.Getenv("FC_FATAL_RECEIPT_DIR")}
	observer.value = fatalRecord{Schema: 1, Invocation: os.Getenv("INVOCATION_ID"), PID: os.Getpid(), LastStage: "STARTUP", DirectoryGeneration: "ABSENT_V1", CredentialSnapshot: "STARTUP_NOT_AUTHORIZATION", Lifecycle: "STARTUP"}
	if info, ok := debug.ReadBuildInfo(); ok {
		for _, setting := range info.Settings {
			if setting.Key == "vcs.revision" {
				observer.value.Source = setting.Value
			}
		}
	}
	if file, err := os.Open("/proc/self/exe"); err == nil {
		digest := sha256.New()
		_, err = io.Copy(digest, file)
		file.Close()
		if err == nil {
			observer.value.Binary = hex.EncodeToString(digest.Sum(nil))
		}
	}
	return observer
}

func safeStage(stage string) string {
	switch stage {
	case "STARTUP", "PROFILE", "DIRECTORY", "SEED_CREATE", "SEED_CONNECT", "SEED_READ", "SEED_ADMISSION", "BROKER", "LISTENER", "HTTP_SERVE", "SEED_RUN", "RUN":
		return stage
	}
	return "UNKNOWN"
}

func safeCause(err error) (string, string) {
	ctx := startupdiag.Start(context.Background(), 0)
	startupdiag.Failure(ctx, "STARTUP", err)
	if value := startupdiag.Snapshot(ctx); value.Cause != "NONE" && value.Cause != "UNKNOWN" {
		return value.Cause, "typed"
	}
	if errors.Is(err, net.ErrClosed) {
		return "NET_CLOSED", "net.ErrClosed"
	}
	if errors.Is(err, syscall.ECONNRESET) {
		return "CONNECTION_RESET", "syscall.ECONNRESET"
	}
	var networkError net.Error
	if errors.As(err, &networkError) && networkError.Timeout() {
		return "IO_TIMEOUT", "net.Error"
	}
	var code roombroker.Code
	if errors.As(err, &code) {
		if value := brokerReason(code); value != "unknown" && value != "" {
			return value, "roombroker.Code"
		}
		switch code {
		case "invalid_options", "credentials_rejected", "provider_credentials_unavailable", "listen_failed", "seed_configuration", "seed_busy", "seed_creation_failed", "seed_join_failed", "seed_not_ready", "seed_publication_failed", "seed_publication_rejected", "seed_closed", "entropy_unavailable":
			return string(code), "roombroker.Code"
		}
	}
	return "UNKNOWN", "unknown"
}

func (observer *fatalObserver) stage(stage string) {
	observer.mu.Lock()
	defer observer.mu.Unlock()
	if !observer.sealed {
		observer.value.LastStage = safeStage(stage)
	}
}

func (observer *fatalObserver) valueStage() string {
	observer.mu.Lock()
	defer observer.mu.Unlock()
	return observer.value.LastStage
}

func (observer *fatalObserver) failure(failure bootstrap.SeedFailure) {
	observer.mu.Lock()
	defer observer.mu.Unlock()
	if observer.first || observer.sealed {
		return
	}
	observer.first = true
	observer.value.Stage = safeStage(failure.Stage)
	observer.value.Cause, observer.value.ErrorClass = safeCause(failure.Cause)
	if failure.Stage == "SEED_READ" && sessiontrace.Allowed(failure.CloseSource, sessiontrace.CloseSources) && failure.CloseSource != "" {
		observer.value.SeedCloseSource = failure.CloseSource
		if failure.CloseSource == "SIGNAL_READ" && failure.SignalingRead.Kind != "" {
			value := failure.SignalingRead.Sanitized()
			observer.value.SignalingRead = &value
		}
		if observer.value.Cause == "UNKNOWN" && failure.CloseSource != "UNKNOWN" {
			observer.value.Cause, observer.value.ErrorClass = failure.CloseSource, "sessiontrace.FirstClose"
		}
	}
	observer.value.Generation = failure.Generation
	if failure.ParentError != nil {
		observer.value.Parent, _ = safeCause(failure.ParentError)
	}
	observer.value.Fatal = observer.value.Parent == "" && observer.value.Cause != "CANCELLED"
}

func (observer *fatalObserver) directory(raw []byte) {
	digest := sha256.Sum256(raw)
	observer.mu.Lock()
	defer observer.mu.Unlock()
	if !observer.sealed {
		observer.value.Directory = hex.EncodeToString(digest[:])
		observer.value.Lifecycle = "SEED_PUBLISHED"
	}
}

func (observer *fatalObserver) credentials(credentials familysession.Credentials) {
	var expiry time.Time
	for _, text := range []string{credentials.Certificate, credentials.Authority, credentials.Revocations} {
		block, _ := pem.Decode([]byte(text))
		if block == nil {
			continue
		}
		var until time.Time
		if cert, err := x509.ParseCertificate(block.Bytes); err == nil {
			until = cert.NotAfter
		} else if crl, err := x509.ParseRevocationList(block.Bytes); err == nil {
			until = crl.NextUpdate
		}
		if !until.IsZero() && (expiry.IsZero() || until.Before(expiry)) {
			expiry = until
		}
	}
	observer.mu.Lock()
	defer observer.mu.Unlock()
	observer.value.LimitingExpiry = expiry.UTC()
}

func (observer *fatalObserver) cleanup() {
	observer.mu.Lock()
	defer observer.mu.Unlock()
	if !observer.sealed {
		observer.value.CleanupStarted = true
	}
}

func (observer *fatalObserver) finish(err error, signal string, panicked bool) {
	observer.mu.Lock()
	if observer.sealed {
		observer.mu.Unlock()
		return
	}
	if !observer.first {
		observer.value.Stage = observer.value.LastStage
		if err != nil {
			observer.value.Cause, observer.value.ErrorClass = safeCause(err)
		} else {
			observer.value.Cause, observer.value.ErrorClass = "NONE", "none"
		}
		observer.value.Fatal = err != nil && observer.value.Cause != "CANCELLED"
	}
	observer.value.ExitPath = "normal_stop"
	if err != nil {
		observer.value.ExitPath = "returned_error"
	}
	if signal == "SIGTERM" || signal == "SIGINT" {
		observer.value.Signal = signal
		if !observer.value.Fatal {
			observer.value.ExitPath = "signal"
		}
	}
	if panicked {
		observer.value.ExitPath = "panic"
		if !observer.first {
			observer.value.Cause, observer.value.ErrorClass, observer.value.Fatal = "PANIC", "panic_redacted", true
		}
	}
	observer.value.Timestamp = time.Now().UTC()
	observer.value.ElapsedMS = time.Since(observer.started).Milliseconds()
	observer.value.CleanupCompleted = !panicked
	if !observer.value.LimitingExpiry.IsZero() {
		observer.value.HeadroomSeconds = int64(time.Until(observer.value.LimitingExpiry).Seconds())
	}
	observer.sealed = true
	value := observer.value
	observer.mu.Unlock()
	_ = writeFatalReceipt(observer.dir, value)
}

func writeFatalReceipt(directory string, value fatalRecord) error {
	if !filepath.IsAbs(directory) || !receiptID.MatchString(value.Invocation) {
		return errors.New("receipt_configuration")
	}
	info, err := os.Lstat(directory)
	if err != nil {
		return err
	}
	if !info.IsDir() || info.Mode().Perm() != 0700 {
		return errors.New("receipt_permissions")
	}
	stale, _ := filepath.Glob(filepath.Join(directory, ".application-*"))
	for _, name := range stale {
		_ = os.Remove(name)
	}
	raw, err := json.Marshal(value)
	if err != nil {
		return err
	}
	if len(raw) > 4096 {
		return errors.New("receipt_size")
	}
	file, err := os.CreateTemp(directory, ".application-")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	_, err = file.Write(append(raw, '\n'))
	if err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	target := filepath.Join(directory, "application-"+value.Invocation+".json")
	if err = os.Link(file.Name(), target); err != nil {
		return err
	}
	entries, err := os.ReadDir(directory)
	if err != nil {
		return err
	}
	type entry struct {
		name     string
		modified time.Time
	}
	var files []entry
	for _, item := range entries {
		if receiptName.MatchString(item.Name()) {
			if info, err := item.Info(); err == nil && info.Mode().IsRegular() {
				files = append(files, entry{item.Name(), info.ModTime()})
			}
		}
	}
	sort.Slice(files, func(left, right int) bool {
		if files[left].modified.Equal(files[right].modified) {
			return files[left].name < files[right].name
		}
		return files[left].modified.Before(files[right].modified)
	})
	for len(files) > 32 {
		_ = os.Remove(filepath.Join(directory, files[0].name))
		files = files[1:]
	}
	if folder, err := os.Open(directory); err == nil {
		defer folder.Close()
		return folder.Sync()
	}
	return nil
}
