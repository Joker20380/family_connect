package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

const fixedConfiguration = "/etc/fc-publisher-recovery-worker.json"

type configuration struct {
	Schema                  int                           `json:"schema"`
	Family                  string                        `json:"family"`
	Gateway                 string                        `json:"gateway"`
	Target                  string                        `json:"target"`
	Staging                 string                        `json:"staging"`
	Attempt                 string                        `json:"attempt"`
	Rollback                string                        `json:"rollback"`
	Lifetime                int                           `json:"lifetime"`
	Expires                 int64                         `json:"expires"`
	Previous                bootstrap.RecoveryPredecessor `json:"previous"`
	Profile                 string                        `json:"profile"`
	ProfileSHA256           string                        `json:"profile_sha256"`
	AuthoritySHA256         string                        `json:"authority_sha256"`
	Locator                 string                        `json:"locator"`
	LocatorSHA256           string                        `json:"locator_sha256"`
	PublisherContractSHA256 string                        `json:"publisher_contract_sha256"`
	GatewayUnit             string                        `json:"gateway_unit"`
}

func readConfiguration(path string) (configuration, error) {
	var config configuration
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0640 || info.Size() > 8192 {
		return config, errors.New("recovery_configuration")
	}
	metadata, ok := info.Sys().(*syscall.Stat_t)
	if !ok || metadata.Uid != 0 || metadata.Nlink != 1 {
		return config, errors.New("recovery_configuration")
	}
	file, err := os.Open(path)
	if err != nil {
		return config, errors.New("recovery_configuration")
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	decoder.DisallowUnknownFields()
	if decoder.Decode(&config) != nil || decoder.Decode(new(any)) != io.EOF || config.Schema != 1 || config.Lifetime != 14400 || config.Expires <= time.Now().Unix() || config.Expires > time.Now().Unix()+1800 {
		return config, errors.New("recovery_configuration")
	}
	for _, path := range []string{config.Target, config.Staging, config.Attempt, config.Rollback, config.Profile, config.Locator} {
		if !filepath.IsAbs(path) || filepath.Clean(path) != path {
			return config, errors.New("recovery_configuration")
		}
	}
	if config.Target == config.Staging || config.Target == config.Profile || config.Staging == config.Profile ||
		filepath.Dir(config.Staging) != filepath.Dir(config.Attempt) || filepath.Dir(config.Staging) != filepath.Dir(config.Rollback) ||
		os.Geteuid() != int(config.Previous.UID) || os.Getegid() != int(config.Previous.GID) {
		return config, errors.New("recovery_configuration")
	}
	return config, nil
}

func run(action string) error {
	config, err := readConfiguration(fixedConfiguration)
	if err != nil {
		return err
	}
	if err = validateBinding(config, time.Now()); err != nil {
		return err
	}
	if !regexp.MustCompile(`^[A-Za-z0-9_.@-]+\.service$`).MatchString(config.GatewayUnit) {
		return errors.New("recovery_unit")
	}
	state, err := exec.Command("/usr/bin/systemctl", "show", config.GatewayUnit, "--property=ActiveState,MainPID").Output()
	if err != nil || !strings.Contains(string(state), "ActiveState=inactive\n") || !strings.Contains(string(state), "MainPID=0\n") {
		return errors.New("recovery_reader_active")
	}
	return execute(config, action, func() (roombroker.RoomProvider, error) { return roombroker.NewTelemostRoomProvider() }, bootstrap.TelemostSeed, validateBinding)
}

func syncParent(path string) error {
	parent, err := os.Open(filepath.Dir(path))
	if err != nil {
		return err
	}
	defer parent.Close()
	return parent.Sync()
}

func execute(config configuration, action string, providerFactory func() (roombroker.RoomProvider, error), connect bootstrap.SeedConnector, validate func(configuration, time.Time) error) error {
	live := &bootstrap.Cache{Path: config.Target, Family: config.Family, Gateway: config.Gateway}
	if action == "rollback" {
		original, err := os.ReadFile(config.Rollback)
		if err != nil || digest(original) != config.Previous.SHA256 {
			return errors.New("recovery_rollback_binding")
		}
		staged, err := os.ReadFile(config.Staging)
		if err != nil {
			return errors.New("recovery_rollback_binding")
		}
		marker, err := os.ReadFile(config.Attempt + ".promotion")
		if err != nil || string(marker) != "ONE_PUBLICATION_ATTEMPT\n" {
			return errors.New("recovery_rollback_binding")
		}
		info, err := os.Lstat(config.Target)
		if err != nil {
			return err
		}
		metadata, ok := info.Sys().(*syscall.Stat_t)
		if !ok {
			return errors.New("recovery_rollback_binding")
		}
		current := bootstrap.RecoveryPredecessor{SHA256: digest(staged), UID: config.Previous.UID, GID: config.Previous.GID, Device: metadata.Dev, Inode: metadata.Ino}
		var previous bootstrap.Directory
		if json.Unmarshal(original, &previous) != nil {
			return errors.New("recovery_rollback_binding")
		}
		if err = live.StoreRecovery(original, previous.IssuedAt.Add(time.Nanosecond), current); err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"result": "ROLLED_BACK_EXPIRED_EVIDENCE_NOT_READY", "sha256": config.Previous.SHA256})
	}
	if action == "stage" {
		return live.WithRecoveryPredecessor(config.Previous, func() error {
			attempt, err := os.OpenFile(config.Attempt, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
			if err != nil {
				return errors.New("recovery_already_attempted")
			}
			if _, err = attempt.WriteString("ONE_ROOM_CREATION_ATTEMPT\n"); err == nil {
				err = attempt.Sync()
			}
			attempt.Close()
			if err != nil {
				return err
			}
			if err = syncParent(config.Attempt); err != nil {
				return err
			}
			provider, err := providerFactory()
			if err != nil {
				return err
			}
			ctx, cancel := context.WithTimeout(context.Background(), 75*time.Second)
			defer cancel()
			room, err := provider.CreateRoom(ctx)
			if err != nil {
				return err
			}
			roomRecord, err := os.OpenFile(config.Attempt, os.O_WRONLY|os.O_APPEND, 0)
			if err != nil {
				return err
			}
			if err = json.NewEncoder(roomRecord).Encode(room); err == nil {
				err = roomRecord.Sync()
			}
			roomRecord.Close()
			if err != nil {
				return err
			}
			ready, stop := context.WithTimeout(ctx, bootstrap.ConnectTimeout)
			carrier, err := connect(ctx, ready, room)
			readyErr := ready.Err()
			stop()
			if err != nil || readyErr != nil || carrier == nil {
				if carrier != nil {
					carrier.Close()
				}
				return errors.New("recovery_room_not_ready")
			}
			defer carrier.Close()
			now := time.Now().UTC()
			directory := bootstrap.Directory{Version: 1, Family: config.Family, IssuedAt: now, ExpiresAt: now.Add(time.Duration(config.Lifetime) * time.Second),
				Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: room.JoinURL, Gateway: config.Gateway}}}
			raw, err := json.Marshal(directory)
			if err != nil {
				return err
			}
			staging := &bootstrap.Cache{Path: config.Staging, Family: config.Family, Gateway: config.Gateway}
			if err = staging.Store(raw, now); err != nil {
				return err
			}
			if err = validate(config, time.Now()); err != nil {
				return err
			}
			hash := sha256.Sum256(raw)
			return json.NewEncoder(os.Stdout).Encode(map[string]any{"result": "STAGED_ROOM_READY", "sha256": hex.EncodeToString(hash[:])})
		})
	}
	if action == "promote" {
		raw, err := os.ReadFile(config.Staging)
		if err != nil {
			return err
		}
		marker := config.Attempt + ".promotion"
		attempt, err := os.OpenFile(marker, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			return errors.New("recovery_promotion_already_attempted")
		}
		if _, err = attempt.WriteString("ONE_PUBLICATION_ATTEMPT\n"); err == nil {
			err = attempt.Sync()
		}
		attempt.Close()
		if err != nil {
			return err
		}
		if err = syncParent(marker); err != nil {
			return err
		}
		if err = live.StoreRecovery(raw, time.Now(), config.Previous); err != nil {
			return err
		}
		if err = validate(config, time.Now()); err != nil {
			return err
		}
		hash := sha256.Sum256(raw)
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"result": "DIRECTORY_PUBLISHED", "sha256": hex.EncodeToString(hash[:])})
	}
	return errors.New("recovery_action")
}

func allowedAction(arguments []string) bool {
	return len(arguments) == 1 && (arguments[0] == "stage" || arguments[0] == "promote" || arguments[0] == "rollback" || arguments[0] == "--help")
}

func main() {
	if !allowedAction(os.Args[1:]) {
		fmt.Fprintln(os.Stderr, "recovery_action")
		os.Exit(2)
	}
	if os.Args[1] == "--help" {
		fmt.Println("Fixed-configuration one-generation publisher recovery: stage | promote | rollback. No caller paths or join URLs.")
		return
	}
	if err := run(os.Args[1]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
