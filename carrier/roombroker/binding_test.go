package roombroker

import (
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type packets struct {
	incoming, outgoing chan []byte
	stopped            chan struct{}
	once               *sync.Once
}

func (pipe packets) Close() error { pipe.once.Do(func() { close(pipe.stopped) }); return nil }
func (pipe packets) SendContext(ctx context.Context, raw []byte) error {
	select {
	case pipe.outgoing <- append([]byte(nil), raw...):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-pipe.stopped:
		return Code("closed")
	}
}
func (pipe packets) Recv(ctx context.Context) ([]byte, error) {
	select {
	case raw := <-pipe.incoming:
		return raw, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-pipe.stopped:
		return nil, Code("closed")
	}
}

func TestBoundSetupOverExistingFamilyTLS(t *testing.T) {
	directory := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if directory == "" {
		t.Skip("requires disposable ProductStore profiles")
	}
	clientRaw, err := os.ReadFile(filepath.Join(directory, "valid.json"))
	if err != nil {
		t.Fatal(err)
	}
	serverRaw, err := os.ReadFile(filepath.Join(directory, "gateway.json"))
	if err != nil {
		t.Fatal(err)
	}
	var credentials familysession.Credentials
	if json.Unmarshal(clientRaw, &credentials) != nil {
		t.Fatal("credentials")
	}
	cert, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil {
		t.Fatal(err)
	}
	key := cert.PrivateKey.(ed25519.PrivateKey)
	var identity Identity
	copy(identity.PublicKey[:], key.Public().(ed25519.PublicKey))
	for _, mode := range []string{"valid", "other_setup", "other_device", "replayed_proof"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			incoming, outgoing := make(chan []byte, 256), make(chan []byte, 256)
			stop := make(chan struct{})
			once := new(sync.Once)
			clientPipe := packets{incoming, outgoing, stop, once}
			serverPipe := packets{outgoing, incoming, stop, once}
			defer clientPipe.Close()
			result := make(chan error, 1)
			release := make(chan struct{})
			defer close(release)
			go func() {
				secured, err := familysession.Open(ctx, serverPipe, serverRaw, true)
				if err != nil {
					result <- err
					return
				}
				defer secured.Close()
				result <- bindGateway(ctx, secured, "setup", identity, func() error { return nil })
				<-release
			}()
			secured, err := familysession.Open(ctx, clientPipe, clientRaw, false)
			if err != nil {
				t.Fatal(err)
			}
			defer secured.Close()
			if mode == "valid" {
				if err := BindClient(ctx, secured, Descriptor{SetupID: "setup"}, clientRaw); err != nil {
					t.Fatal(err)
				}
			} else {
				nonce, err := secured.Recv(ctx)
				if err != nil {
					t.Fatal(err)
				}
				id := "setup"
				signer := key
				if mode == "other_setup" {
					id = "different"
				}
				if mode == "other_device" {
					_, signer, err = ed25519.GenerateKey(nil)
					if err != nil {
						t.Fatal(err)
					}
				}
				if mode == "replayed_proof" {
					nonce = make([]byte, 32)
				}
				if err := secured.SendContext(ctx, ed25519.Sign(signer, bindingMessage(id, nonce))); err != nil {
					t.Fatal(err)
				}
			}
			err = <-result
			if (mode == "valid") != (err == nil) {
				t.Fatal("binding result", mode, err)
			}
		})
	}
}
