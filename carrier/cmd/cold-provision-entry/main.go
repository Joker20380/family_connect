package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type options struct {
	profile, anchor, backend, node, state string
	duration                              time.Duration
}

type safeLog struct{}

func (safeLog) Write(raw []byte) (int, error) {
	if strings.HasPrefix(string(raw), "cold_provision ") {
		_, _ = os.Stdout.Write(raw)
	}
	return len(raw), nil
}

func exclusive(path string, raw []byte) error {
	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	defer file.Close()
	if _, err = file.Write(raw); err != nil {
		return err
	}
	return file.Sync()
}

func configuration(value options) (coldprovision.Config, coldprovision.Backend, error) {
	var config coldprovision.Config
	if value.node != "nl-amsterdam-1" && value.node != "nl-amsterdam-2" ||
		value.duration <= 0 || value.duration > 7*time.Minute || !filepath.IsAbs(value.state) {
		return config, nil, coldprovision.ErrRejected
	}
	backend, err := entryBackend(value.backend)
	if err != nil {
		return config, nil, err
	}
	raw, err := roombroker.LoadCredentials(value.profile)
	if err != nil {
		return config, nil, err
	}
	defer clear(raw)
	tlsConfig, _, err := familysession.Configuration(raw, true)
	if err != nil {
		return config, nil, err
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return config, nil, coldprovision.ErrRejected
	}
	anchor, err := os.ReadFile(value.anchor)
	if err != nil || len(anchor) > 128 {
		return config, nil, coldprovision.ErrRejected
	}
	anchor, err = base64.StdEncoding.Strict().DecodeString(strings.TrimSpace(string(anchor)))
	if err != nil || len(anchor) != 32 {
		return config, nil, coldprovision.ErrRejected
	}
	config = coldprovision.Config{Anchor: anchor, Node: value.node, Family: credentials.Family,
		Gateway: credentials.Gateway, Identity: tlsConfig.Certificates[0], Lifetime: value.duration}
	return config, backend, nil
}

func verifyLocator(path, anchorPath, node string) error {
	raw, err := os.ReadFile(path)
	if err != nil || len(raw) > 16384 {
		return coldprovision.ErrRejected
	}
	anchor, err := os.ReadFile(anchorPath)
	if err != nil || len(anchor) > 128 {
		return coldprovision.ErrRejected
	}
	anchor, err = base64.StdEncoding.Strict().DecodeString(strings.TrimSpace(string(anchor)))
	if err != nil {
		return coldprovision.ErrRejected
	}
	address, _, err := coldprovision.Verify(raw, anchor, node, time.Now())
	if err != nil {
		return err
	}
	digest := sha256.Sum256(raw)
	return json.NewEncoder(os.Stdout).Encode(map[string]any{"node": node, "expires_at": address.ExpiresAt,
		"locator_sha256": hex.EncodeToString(digest[:])})
}

func serve(parent context.Context, value options, provider roombroker.RoomProvider, connector bootstrap.SeedConnector) error {
	config, backend, err := configuration(value)
	if err != nil {
		return err
	}
	if err = os.Mkdir(value.state, 0700); err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(parent, value.duration)
	defer cancel()
	defer func() { _ = exclusive(filepath.Join(value.state, "stopped.json"), []byte("{\"stopped\":true}\n")) }()
	config.Publish = func(directory bootstrap.Directory) ([]byte, error) {
		raw, err := json.Marshal(directory)
		if err != nil {
			return nil, err
		}
		if err = exclusive(filepath.Join(value.state, "seed.json"), raw); err != nil {
			return nil, err
		}
		fmt.Println("SEED_CONNECTED_AWAITING_EXISTING_ISSUER")
		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()
		for {
			info, err := os.Lstat(filepath.Join(value.state, "locator.json"))
			if err == nil {
				if !info.Mode().IsRegular() || info.Size() > 16384 || info.Mode().Perm()&0022 != 0 {
					return nil, coldprovision.ErrRejected
				}
				locator, err := os.ReadFile(filepath.Join(value.state, "locator.json"))
				if err != nil {
					return nil, err
				}
				address, _, err := coldprovision.Verify(locator, config.Anchor, config.Node, time.Now())
				if err != nil || len(directory.Seeds) != 1 || address.Room != directory.Seeds[0].JoinURL ||
					address.ExpiresAt > directory.ExpiresAt.Unix() {
					return nil, coldprovision.ErrRejected
				}
				certificate, _ := pem.Decode([]byte(address.ServerCertificate))
				if certificate == nil || !bytes.Equal(certificate.Bytes, config.Identity.Certificate[0]) {
					return nil, coldprovision.ErrRejected
				}
				digest := sha256.Sum256(locator)
				ready, _ := json.Marshal(map[string]any{"phase": "LOCATOR_VERIFIED_SEED_CONNECTED", "pid": os.Getpid(),
					"observed_at": time.Now().Unix(), "expires_at": address.ExpiresAt, "locator_sha256": hex.EncodeToString(digest[:])})
				if err = exclusive(filepath.Join(value.state, "ready.json"), ready); err != nil {
					return nil, err
				}
				fmt.Println("LOCATOR_VERIFIED_SEED_CONNECTED")
				return locator, nil
			}
			if !errors.Is(err, os.ErrNotExist) {
				return nil, err
			}
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-ticker.C:
			}
		}
	}
	return coldprovision.Run(ctx, config, provider, connector, backend)
}

func main() {
	log.SetFlags(0)
	log.SetOutput(safeLog{})
	var value options
	flag.StringVar(&value.profile, "profile", "", "existing private gateway profile")
	flag.StringVar(&value.anchor, "anchor", "", "existing public ControlTrust anchor")
	flag.StringVar(&value.backend, "backend", authorityURL, "existing authority HTTPS or disposable loopback handlers")
	flag.StringVar(&value.node, "node", "nl-amsterdam-1", "existing selected node")
	flag.StringVar(&value.state, "state", "", "new private invocation directory")
	flag.DurationVar(&value.duration, "duration", 7*time.Minute, "bounded one-entry lifetime, at most 7m")
	check := flag.Bool("check", false, "validate configuration without provider calls or creating state")
	locator := flag.String("verify-locator", "", "verify public locator without provider calls or private profile")
	flag.Parse()
	if *locator != "" {
		if err := verifyLocator(*locator, value.anchor, value.node); err != nil {
			fmt.Fprintln(os.Stderr, "LOCATOR_REJECTED")
			os.Exit(1)
		}
		return
	}
	if _, _, err := configuration(value); err != nil {
		fmt.Fprintln(os.Stderr, "ENTRY_CONFIGURATION_REJECTED")
		os.Exit(1)
	}
	if *check {
		fmt.Println("CONFIGURATION_VALID_NO_PROVIDER_CALL")
		return
	}
	provider, err := roombroker.NewTelemostRoomProvider()
	if err != nil {
		fmt.Fprintln(os.Stderr, "PROVIDER_CREDENTIAL_UNAVAILABLE")
		os.Exit(1)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err = serve(ctx, value, provider, bootstrap.TelemostSeed); err != nil && ctx.Err() == nil {
		fmt.Fprintln(os.Stderr, "ENTRY_STOPPED_ERROR_PRIVATE_DETAIL_SUPPRESSED")
		os.Exit(1)
	}
	fmt.Println("ENTRY_STOPPED")
}
