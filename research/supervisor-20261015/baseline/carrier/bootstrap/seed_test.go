package bootstrap

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestSeedPublishedOnlyAfterReadyAndWithdrawn(test *testing.T) {
	exported := make(chan Directory, 1)
	manager := &SeedManager{Publish: func(directory Directory) error { exported <- directory; return nil }}
	ctx, cancel := context.WithDeadline(context.Background(), time.Now().In(time.FixedZone("non-UTC", 3*3600)).Add(20*time.Second))
	defer cancel()
	started, ready := make(chan struct{}), make(chan struct{})
	client, server := pair()
	defer client.Close()
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			return roombroker.Room{ID: "seed", JoinURL: "https://telemost.yandex.ru/j/seed-test"}, nil
		}),
			func(ctx, bound context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
				close(started)
				select {
				case <-ready:
					return server, nil
				case <-bound.Done():
					return nil, bound.Err()
				}
			}, testFamily, testGateway, time.Minute, func(context.Context, familysession.PacketEndpoint) {})
	}()
	<-started
	manager.mu.Lock()
	published := manager.directory != nil
	manager.mu.Unlock()
	if published {
		test.Fatal("seed published before READY")
	}
	select {
	case <-exported:
		test.Fatal("seed exported before READY")
	default:
	}
	close(ready)
	for {
		manager.mu.Lock()
		published = manager.directory != nil
		manager.mu.Unlock()
		if published {
			break
		}
		select {
		case <-ctx.Done():
			test.Fatal("seed not published")
		case <-time.After(time.Millisecond):
		}
	}
	select {
	case directory := <-exported:
		if len(directory.Seeds) != 1 || directory.Seeds[0].Gateway != testGateway {
			test.Fatal("invalid export")
		}
		if directory.IssuedAt.Location() != time.UTC || directory.ExpiresAt.Location() != time.UTC {
			test.Fatal("producer retained local timezone")
		}
		var value map[string]any
		if json.Unmarshal(encode(directory), &value) != nil || !strings.HasSuffix(value["issued_at"].(string), "Z") || !strings.HasSuffix(value["expires_at"].(string), "Z") {
			test.Fatal("noncanonical producer output")
		}
		test.Run("PythonPublicationContract", func(test *testing.T) {
			python, artifact := os.Getenv("FC_TEST_PYTHON"), os.Getenv("FC_TEST_SYNC_ARTIFACT")
			if python == "" || artifact == "" {
				test.Skip("isolated Python artifact required")
			}
			program := `import contextlib,io,json,runpy,sys
sys.argv=[sys.argv[1],"--help"]
with contextlib.redirect_stdout(io.StringIO()):
 try:runpy.run_path(sys.argv[0],run_name="__main__")
 except SystemExit as error:assert error.code==0
from control.friends.restricted import directory,timestamp_ns
raw=sys.stdin.buffer.read();value=json.loads(raw)
value=directory(raw,value["family"],value["seeds"][0]["gateway"],now_ns=timestamp_ns(value["issued_at"]))
sys.stdout.write(json.dumps(value,separators=(",",":")))
`
			command := exec.CommandContext(ctx, python, "-I", "-c", program, artifact)
			command.Dir = test.TempDir()
			command.Stdin = bytes.NewReader(encode(directory))
			raw, err := command.Output()
			if err != nil {
				test.Fatal("serialized real SeedManager publication rejected by isolated Python")
			}
			if _, err := ParseDirectory(raw, testFamily, testGateway, directory.IssuedAt); err != nil {
				test.Fatal("Python publication rejected by native consumer")
			}
		})
	case <-ctx.Done():
		test.Fatal("seed was not exported")
	}
	cancel()
	<-done
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if manager.directory != nil || manager.running {
		test.Fatal("seed survived shutdown")
	}
}

func TestSeedFailureAndNotReady(test *testing.T) {
	for _, kind := range []string{"provider", "ready", "cancel"} {
		test.Run(kind, func(test *testing.T) {
			manager := &SeedManager{}
			ctx, cancel := context.WithCancel(bounded(test))
			defer cancel()
			if kind == "cancel" {
				cancel()
			}
			err := manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
				if kind == "provider" {
					return roombroker.Room{}, errors.New("provider")
				}
				return roombroker.Room{ID: "seed", JoinURL: "https://telemost.yandex.ru/j/seed-test"}, nil
			}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				return nil, errors.New("not READY")
			}, testFamily, testGateway, time.Minute, func(context.Context, familysession.PacketEndpoint) {})
			if err == nil || manager.directory != nil || manager.running {
				test.Fatal("unavailable seed published")
			}
		})
	}
}
