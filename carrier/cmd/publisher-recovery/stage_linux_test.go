package main

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type testProvider struct{ calls int }

func (provider *testProvider) CreateRoom(context.Context) (roombroker.Room, error) {
	provider.calls++
	return roombroker.Room{ID: "synthetic-room", JoinURL: "https://telemost.yandex.ru/j/synthetic-recovery"}, nil
}

type testEndpoint struct{ closed bool }

func (*testEndpoint) SendContext(context.Context, []byte) error { return nil }
func (*testEndpoint) Recv(context.Context) ([]byte, error)      { return nil, errors.New("unused") }
func (endpoint *testEndpoint) Close() error                     { endpoint.closed = true; return nil }

func stageFixture(t *testing.T) (configuration, []byte, func(configuration, time.Time) error) {
	t.Helper()
	profile, config, now := bindingFixture(t)
	root := t.TempDir()
	config.Profile = filepath.Join(root, "profile.json")
	config.Target = filepath.Join(root, "directory.json")
	config.Staging = filepath.Join(root, "staged.json")
	config.Attempt = filepath.Join(root, "attempt")
	config.Rollback = filepath.Join(root, "previous-directory.json")
	config.Lifetime = 14400
	profileRaw, _ := json.Marshal(profile)
	if err := os.WriteFile(config.Profile, profileRaw, 0600); err != nil {
		t.Fatal(err)
	}
	directory := bootstrap.Directory{Version: 1, Family: config.Family, IssuedAt: now.Add(-5 * time.Hour), ExpiresAt: now.Add(-time.Hour),
		Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/old-synthetic", Gateway: config.Gateway}}}
	raw, _ := json.Marshal(directory)
	if err := os.WriteFile(config.Target, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(config.Rollback, raw, 0600); err != nil {
		t.Fatal(err)
	}
	info, _ := os.Stat(config.Target)
	metadata := info.Sys().(*syscall.Stat_t)
	config.Previous = bootstrap.RecoveryPredecessor{SHA256: digest(raw), UID: metadata.Uid, GID: metadata.Gid, Device: metadata.Dev, Inode: metadata.Ino}
	validate := func(actual configuration, instant time.Time) error {
		current, err := os.ReadFile(actual.Profile)
		if err != nil {
			return err
		}
		return historicalBinding(current, actual, instant)
	}
	return config, raw, validate
}

func TestOneRoomStagingNoLiveWriteAndSingleAtomicPromotion(t *testing.T) {
	config, before, validate := stageFixture(t)
	provider := &testProvider{}
	endpoint := &testEndpoint{}
	factory := func() (roombroker.RoomProvider, error) { return provider, nil }
	connect := func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
		return endpoint, nil
	}
	profileBefore, _ := os.ReadFile(config.Profile)
	if err := execute(config, "stage", factory, connect, validate); err != nil {
		t.Fatal(err)
	}
	live, _ := os.ReadFile(config.Target)
	if string(live) != string(before) || provider.calls != 1 || !endpoint.closed {
		t.Fatal("staging side effect")
	}
	staged, _ := os.ReadFile(config.Staging)
	directory, err := bootstrap.ParseDirectory(staged, config.Family, config.Gateway, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	var fields map[string]any
	if json.Unmarshal(staged, &fields) != nil || len(fields) != 5 || directory.Version != 1 || len(directory.Seeds) != 1 || directory.Seeds[0].Transport != "telemost-webrtc" || directory.ExpiresAt.Sub(directory.IssuedAt) != 4*time.Hour {
		t.Fatal("directory schema")
	}
	if err = execute(config, "stage", factory, connect, validate); err == nil || provider.calls != 1 {
		t.Fatal("room replay")
	}
	if err = execute(config, "promote", factory, connect, validate); err != nil {
		t.Fatal(err)
	}
	live, _ = os.ReadFile(config.Target)
	if string(live) != string(staged) {
		t.Fatal("promotion readback")
	}
	if err = execute(config, "promote", factory, connect, validate); err == nil || provider.calls != 1 {
		t.Fatal("publication replay")
	}
	profileAfter, _ := os.ReadFile(config.Profile)
	if string(profileBefore) != string(profileAfter) {
		t.Fatal("profile/crl/floor written")
	}
	if err = execute(config, "rollback", factory, connect, validate); err != nil {
		t.Fatal(err)
	}
	live, _ = os.ReadFile(config.Target)
	if string(live) != string(before) {
		t.Fatal("rollback evidence changed")
	}
	if _, err = bootstrap.ParseDirectory(live, config.Family, config.Gateway, time.Now()); err == nil {
		t.Fatal("rollback marked current")
	}
	if err = execute(config, "rollback", factory, connect, validate); err == nil {
		t.Fatal("second rollback accepted")
	}
}

func TestNoStagingOrPublicationWithoutRoomReady(t *testing.T) {
	config, before, validate := stageFixture(t)
	provider := &testProvider{}
	err := execute(config, "stage", func() (roombroker.RoomProvider, error) { return provider, nil },
		func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			return nil, errors.New("synthetic join failure")
		}, validate)
	if err == nil || provider.calls != 1 {
		t.Fatal("room not ready accepted")
	}
	if _, err = os.Stat(config.Staging); !os.IsNotExist(err) {
		t.Fatal("staged invalid room")
	}
	live, _ := os.ReadFile(config.Target)
	if string(live) != string(before) {
		t.Fatal("live write")
	}
}

func TestCallerCannotChoosePathsFamilyGatewayOrJoinURL(t *testing.T) {
	for _, arguments := range [][]string{{"stage", "--path", "other"}, {"stage", "--join-url", "https://telemost.yandex.ru/j/other"},
		{"stage", "--family", "other"}, {"stage", "--gateway", "other"}, {"--config", "other"}, {"stage", "other"}, {}} {
		if allowedAction(arguments) {
			t.Fatal("caller controlled recovery")
		}
	}
	if !allowedAction([]string{"stage"}) || !allowedAction([]string{"promote"}) || !allowedAction([]string{"--help"}) {
		t.Fatal("fixed actions")
	}
}

func TestFixedConfigurationRejectsUnsafeLifetimeAndFields(t *testing.T) {
	config, _, _ := stageFixture(t)
	config.Schema = 1
	config.Expires = time.Now().Unix() + 900
	config.Locator = filepath.Join(t.TempDir(), "locator.json")
	for _, fault := range []string{"valid", "lifetime", "expired", "future", "join_url", "unknown_path", "writable", "symlink"} {
		t.Run(fault, func(t *testing.T) {
			root := t.TempDir()
			path := filepath.Join(root, "fixed.json")
			raw, _ := json.Marshal(config)
			var fields map[string]any
			json.Unmarshal(raw, &fields)
			switch fault {
			case "lifetime":
				fields["lifetime"] = 14401
			case "expired":
				fields["expires"] = 0
			case "future":
				fields["expires"] = time.Now().Unix() + 3600
			case "join_url":
				fields["join_url"] = "https://telemost.yandex.ru/j/caller"
			case "unknown_path":
				fields["path"] = "/caller"
			}
			raw, _ = json.Marshal(fields)
			if err := os.WriteFile(path, raw, 0640); err != nil {
				t.Fatal(err)
			}
			if fault == "writable" {
				os.Chmod(path, 0660)
			}
			if fault == "symlink" {
				os.Rename(path, path+".original")
				os.Symlink(path+".original", path)
			}
			_, err := readConfiguration(path)
			if (err == nil) != (fault == "valid") {
				t.Fatalf("configuration gate: %v", err)
			}
		})
	}
}
