//go:build seedacceptance && linux

package bootstrap

import (
	"context"
	"encoding/json"
	"io"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/telemost"
)

func acceptanceFixture(test *testing.T, uid uint32) (context.Context, *seedAcceptance, func()) {
	test.Helper()
	directory := test.TempDir()
	if os.Chmod(directory, 0700) != nil {
		test.Fatal("permissions")
	}
	binding, err := acceptanceProcessBinding()
	if err != nil {
		test.Fatal(err)
	}
	config := SeedAcceptanceConfig{Schema: 1, Enabled: true, BinarySHA256: binding.BinarySHA256, Directory: directory, ExpiresAt: time.Now().Add(time.Minute)}
	ctx, stop, err := startSeedAcceptance(context.Background(), config, binding, uid)
	if err != nil {
		test.Fatal(err)
	}
	control := ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
	test.Cleanup(stop)
	return ctx, control, stop
}

func TestAcceptanceRejectBindingAndState(test *testing.T) {
	for _, name := range []string{"binary", "pid", "ticks", "invocation", "generation", "room", "expired", "future", "long_ttl", "before_start", "nonce", "schema", "command", "consumed", "before_active", "recovering", "stale_generation", "stopped"} {
		test.Run(name, func(test *testing.T) {
			_, control, _ := acceptanceFixture(test, uint32(os.Geteuid()))
			session, err := telemost.New(context.Background(), telemost.Config{RoomURL: "https://telemost.yandex.ru/j/12345678901234", Mode: telemost.ModeVP8})
			if err != nil {
				test.Fatal(err)
			}
			defer session.Close()
			control.mu.Lock()
			control.target = &acceptanceTarget{generation: 1, active: func() *telemost.Session { return session }}
			binding := control.binding
			binding.Generation = 1
			binding.RoomHash = session.ResearchRoomHash()
			command := SeedAcceptanceCommand{Schema: 1, Command: acceptanceCommand, Binding: binding, Nonce: strings.Repeat("a", 64), ArmedAt: time.Now(), ExpiresAt: time.Now().Add(10 * time.Second)}
			switch name {
			case "binary":
				command.Binding.BinarySHA256 = strings.Repeat("b", 64)
			case "pid":
				command.Binding.PID++
			case "ticks":
				command.Binding.StartTicks++
			case "invocation":
				command.Binding.InvocationID = "different"
			case "generation":
				command.Binding.Generation++
			case "room":
				command.Binding.RoomHash = strings.Repeat("b", 64)
			case "expired":
				command.ExpiresAt = time.Now().Add(-time.Second)
			case "future":
				command.ArmedAt = time.Now().Add(time.Second)
			case "long_ttl":
				command.ExpiresAt = time.Now().Add(time.Hour)
			case "before_start":
				command.ArmedAt = control.created.Add(-time.Second)
			case "nonce":
				command.Nonce = "bad"
			case "schema":
				command.Schema = 2
			case "command":
				command.Command = "anything"
			case "consumed":
				control.consumed = true
			case "before_active":
				control.target = nil
			case "recovering":
				control.target.active = func() *telemost.Session { return nil }
			case "stale_generation":
				control.target.generation = 2
			case "stopped":
				control.cancel()
			}
			control.mu.Unlock()
			if control.consume(command, time.Now()) {
				test.Fatal("invalid accepted")
			}
			if session.ResearchTriggerObserved() {
				test.Fatal("invalid closed websocket")
			}
		})
	}
}

func TestAcceptanceSocketPermissionsUnprivilegedAndCleanup(test *testing.T) {
	if os.Geteuid() == 0 {
		test.Skip("requires actual non-root SO_PEERCRED")
	}
	_, control, stop := acceptanceFixture(test, 0)
	session, err := telemost.New(context.Background(), telemost.Config{RoomURL: "https://telemost.yandex.ru/j/12345678901234", Mode: telemost.ModeVP8})
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	control.mu.Lock()
	control.target = &acceptanceTarget{generation: 1, active: func() *telemost.Session { return session }}
	binding := control.binding
	binding.Generation = 1
	binding.RoomHash = session.ResearchRoomHash()
	control.mu.Unlock()
	command := SeedAcceptanceCommand{Schema: 1, Command: acceptanceCommand, Binding: binding, Nonce: strings.Repeat("a", 64), ArmedAt: time.Now(), ExpiresAt: time.Now().Add(10 * time.Second)}
	request, err := json.Marshal(command)
	if err != nil {
		test.Fatal(err)
	}
	path := control.listener.Addr().String()
	info, err := os.Stat(path)
	if err != nil || info.Mode().Perm() != 0600 {
		test.Fatal("socket permissions")
	}
	connection, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: path, Net: "unix"})
	if err != nil {
		test.Fatal(err)
	}
	connection.SetDeadline(time.Now().Add(2 * time.Second))
	connection.Write(request)
	connection.CloseWrite()
	raw, _ := io.ReadAll(connection)
	connection.Close()
	if string(raw) != "REJECTED\n" {
		test.Fatal("unauthorized peer accepted")
	}
	stop()
	if _, err = os.Lstat(path); !os.IsNotExist(err) {
		test.Fatal("socket retained")
	}
	if control.consumed {
		test.Fatal("unused control consumed")
	}
}

func TestAcceptanceMalformedAndOversized(test *testing.T) {
	for _, raw := range []string{"", "{", `{"schema":1,"unexpected":true}`, `{"schema":1,"schema":1}`, `{"binding":{"pid":1,"pid":2}}`, `{} {}`, strings.Repeat("x", 2049)} {
		var command SeedAcceptanceCommand
		if strictAcceptanceJSON([]byte(raw), &command) == nil {
			test.Fatal("invalid schema accepted")
		}
	}
}

func TestAcceptanceStorageRetentionPrivacyAndFailure(test *testing.T) {
	directory := test.TempDir()
	foreign := filepath.Join(directory, "preserve.json")
	os.WriteFile(foreign, []byte("PRIVATE_REASON"), 0600)
	for index := 1; index <= 70; index++ {
		receipt := SeedAcceptanceReceipt{Schema: 1, UTC: time.Now().UTC(), State: "CLEANED", Binding: SeedAcceptanceBinding{PID: 123, StartTicks: 456}, NonceHash: strings.Repeat("a", 64)}
		if err := writeAcceptanceReceipt(directory, receipt, index); err != nil {
			test.Fatal(err)
		}
	}
	entries, _ := os.ReadDir(directory)
	if len(entries) != 65 {
		test.Fatal("retention", len(entries))
	}
	for _, entry := range entries {
		info, _ := entry.Info()
		if info.Mode().Perm() != 0600 {
			test.Fatal("file mode")
		}
		if entry.Name() == "preserve.json" {
			continue
		}
		raw, _ := os.ReadFile(filepath.Join(directory, entry.Name()))
		var receipt SeedAcceptanceReceipt
		if json.Unmarshal(raw, &receipt) != nil || strings.Contains(string(raw), "PRIVATE_REASON") {
			test.Fatal("privacy")
		}
	}
	if writeAcceptanceReceipt(filepath.Join(directory, "missing"), SeedAcceptanceReceipt{}, 1) == nil {
		test.Fatal("write failure not surfaced to writer")
	}
	_, control, stop := acceptanceFixture(test, uint32(os.Geteuid()))
	control.emit("READY", false, "PENDING", "PENDING")
	stop()
	if control.consumed {
		test.Fatal("receipt changed protocol")
	}
}

func TestAcceptanceConfigurationAndLifecycle(test *testing.T) {
	ctx := context.Background()
	unchanged, stop, err := StartSeedAcceptance(ctx, "")
	if err != nil || unchanged != ctx {
		test.Fatal("default enabled")
	}
	stop()
	for _, name := range []string{"wrong_hash", "disabled", "expired", "long_window", "directory_mode", "occupied_socket"} {
		test.Run(name, func(test *testing.T) {
			directory := test.TempDir()
			os.Chmod(directory, 0700)
			binding, err := acceptanceProcessBinding()
			if err != nil {
				test.Fatal(err)
			}
			config := SeedAcceptanceConfig{Schema: 1, Enabled: true, BinarySHA256: binding.BinarySHA256, Directory: directory, ExpiresAt: time.Now().Add(time.Minute)}
			switch name {
			case "wrong_hash":
				config.BinarySHA256 = "bad"
			case "disabled":
				config.Enabled = false
			case "expired":
				config.ExpiresAt = time.Now().Add(-time.Second)
			case "long_window":
				config.ExpiresAt = time.Now().Add(time.Hour)
			case "directory_mode":
				os.Chmod(directory, 0755)
			case "occupied_socket":
				os.WriteFile(filepath.Join(directory, "seed-acceptance.sock"), []byte("preserve"), 0600)
			}
			if _, stop, err := startSeedAcceptance(ctx, config, binding, uint32(os.Geteuid())); err == nil {
				stop()
				test.Fatal("unsafe config accepted")
			}
		})
	}
	path := filepath.Join(test.TempDir(), "config.json")
	os.WriteFile(path, []byte(`{}`), 0600)
	if _, err := readAcceptanceConfig(path); err == nil {
		test.Fatal("non-root/untrusted path accepted")
	}
	symlink := path + ".link"
	os.Symlink(path, symlink)
	if _, err := readAcceptanceConfig(symlink); err == nil {
		test.Fatal("symlink config")
	}
	if trustedAcceptanceParents(path, 0) {
		test.Fatal("world-writable ancestry")
	}
	_, control, finish := acceptanceFixture(test, uint32(os.Geteuid()))
	connection, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: control.listener.Addr().String(), Net: "unix"})
	if err != nil {
		test.Fatal(err)
	}
	connection.Write([]byte("{"))
	connection.Close()
	finish()
	if control.consumed {
		test.Fatal("helper crash caused trigger")
	}
}

func TestAcceptanceUnusedExpiry(test *testing.T) {
	directory := test.TempDir()
	os.Chmod(directory, 0700)
	binding, err := acceptanceProcessBinding()
	if err != nil {
		test.Fatal(err)
	}
	ctx, finish, err := startSeedAcceptance(context.Background(), SeedAcceptanceConfig{Schema: 1, Enabled: true, BinarySHA256: binding.BinarySHA256, Directory: directory, ExpiresAt: time.Now().Add(30 * time.Millisecond)}, binding, uint32(os.Geteuid()))
	if err != nil {
		test.Fatal(err)
	}
	control := ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
	select {
	case <-control.done:
	case <-time.After(time.Second):
		test.Fatal("control not expired")
	}
	finish()
	if ctx.Err() != nil {
		test.Fatal("control expiry cancelled service context")
	}
	if control.consumed {
		test.Fatal("expiry triggered")
	}
	if _, err := os.Stat(filepath.Join(directory, "seed-acceptance.sock")); !os.IsNotExist(err) {
		test.Fatal("expiry cleanup")
	}
}

func TestAcceptanceRootPolicyEntry(test *testing.T) {
	if os.Geteuid() != 0 {
		test.Skip("root-only positive policy test requires explicit local authorization")
	}
	directory, err := os.MkdirTemp("/run", "fc-seed-acceptance-local-")
	if err != nil {
		test.Fatal(err)
	}
	defer os.RemoveAll(directory)
	os.Chmod(directory, 0700)
	binding, err := acceptanceProcessBinding()
	if err != nil {
		test.Fatal(err)
	}
	config := SeedAcceptanceConfig{Schema: 1, Enabled: true, BinarySHA256: binding.BinarySHA256, Directory: directory, ExpiresAt: time.Now().Add(time.Minute)}
	raw, _ := json.Marshal(config)
	path := filepath.Join(directory, "policy.json")
	if os.WriteFile(path, raw, 0600) != nil {
		test.Fatal("write fixture policy")
	}
	parent, cancel := context.WithCancel(context.Background())
	defer cancel()
	ctx, finish, err := StartSeedAcceptance(parent, path)
	if err != nil {
		test.Fatal(err)
	}
	control := ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
	if control.binding != binding {
		test.Fatal("process binding")
	}
	finish()
	if parent.Err() != nil {
		test.Fatal("control cleanup cancelled parent")
	}
	for _, mode := range []os.FileMode{0644, 0660, 0666} {
		os.Chmod(path, mode)
		if _, err := readAcceptanceConfig(path); err == nil {
			test.Fatal("unsafe root policy mode")
		}
	}
	os.Chmod(path, 0640)
	if _, err := readAcceptanceConfig(path); err != nil {
		test.Fatal("read-only service-group policy")
	}
	test.Log("ROOT_POLICY_ENTRY=PASS ROOT_OWNERSHIP=PASS ROOT_PROCESS_BINDING=PASS CONTROL_CLEANUP=PASS")
}
