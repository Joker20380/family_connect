package qualification

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func provisioningNegatives(test *testing.T, ctx context.Context, root string, provider Provider, locator, anchor, secret, bundle []byte, valid map[string]any, dropSeen, dropRelease chan struct{}) {
	issued := func() string {
		repository, _ := filepath.Abs("../../..")
		command := exec.CommandContext(ctx, os.Getenv("FC_COLD_PROVISION_PYTHON"), filepath.Join(repository, "tests/fixtures/mobile_bootstrap/provision_backend.py"), "inspect", root)
		command.Env = append(os.Environ(), "PYTHONPATH="+repository)
		raw, err := command.Output()
		if err != nil {
			test.Fatal(err)
		}
		return string(raw)
	}
	before := issued()
	test.Run("other_server", func(test *testing.T) {
		certificate, _ := os.ReadFile(filepath.Join(root, "other-server.pem"))
		raw, _ := os.ReadFile(filepath.Join(root, "gateway.json"))
		var credentials familysession.Credentials
		json.Unmarshal(raw, &credentials)
		identity, err := tls.X509KeyPair(certificate, []byte(credentials.PrivateKey))
		if err != nil {
			test.Fatal(err)
		}
		rogue, stop := context.WithTimeout(ctx, 3*time.Second)
		defer stop()
		ready := make(chan string, 1)
		finished := make(chan error, 1)
		manager := bootstrap.SeedManager{Publish: func(directory bootstrap.Directory) error { ready <- directory.Seeds[0].JoinURL; return nil }}
		go func() {
			finished <- manager.Run(rogue, provider, provider.Seed, credentials.Family, credentials.Gateway, time.Minute, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
				coldprovision.Serve(ctx, endpoint, identity, time.Now().Add(time.Minute), "nl-amsterdam-1", func(context.Context, coldprovision.Request) (coldprovision.Reply, error) {
					test.Error("unauthenticated server reached RPC")
					return coldprovision.Reply{}, coldprovision.ErrRejected
				})
			})
		}()
		defer func() { stop(); <-finished }()
		var room string
		select {
		case room = <-ready:
		case <-rogue.Done():
			test.Fatal("rogue seed timeout")
		}
		_, err = coldprovision.Open(rogue, locator, anchor, "nl-amsterdam-1", func(lifetime, ready context.Context, _ roombroker.Room) (familysession.PacketEndpoint, error) {
			return provider.Seed(lifetime, ready, roombroker.Room{JoinURL: room})
		})
		if !errors.Is(err, coldprovision.ErrRejected) {
			test.Fatalf("server pin failure: %v", err)
		}
	})
	open := func() *coldprovision.Client {
		client, err := coldprovision.Open(ctx, locator, anchor, "nl-amsterdam-1", provider.Seed)
		if err != nil {
			test.Fatal(err)
		}
		test.Cleanup(client.Close)
		return client
	}
	post := func(client *coldprovision.Client, path string, body any, id string) (coldprovision.Reply, error) {
		raw, _ := json.Marshal(body)
		bound, _ := json.Marshal(coldprovision.BoundRequest{Gateway: "nl-amsterdam-1", Request: raw})
		return client.Post(path, bound, id)
	}
	challengeBody := map[string]any{"public_identity": valid["public_identity"], "wireguard_public_key": valid["wireguard_public_key"]}
	var negatives map[string]map[string]any
	raw, err := os.ReadFile(filepath.Join(root, "negative-devices.json"))
	if err != nil {
		test.Fatal(err)
	}
	if err = json.Unmarshal(raw, &negatives); err != nil {
		test.Fatal(err)
	}
	for _, name := range []string{"unactivated", "revoked", "subscription_expired"} {
		test.Run(name, func(test *testing.T) {
			client := open()
			defer client.Close()
			reply, err := post(client, coldprovision.Challenge, negatives[name], "10000000000000000000000000000001")
			if err != nil || reply.Status != 403 {
				test.Fatalf("expected real authority denial: status=%d err=%v", reply.Status, err)
			}
		})
	}
	for index, name := range []string{"other_session_replay", "wrong_purpose", "wrong_signature", "other_recipient"} {
		test.Run(name, func(test *testing.T) {
			client := open()
			defer client.Close()
			challenge, err := post(client, coldprovision.Challenge, challengeBody, fmt.Sprintf("%032x", 100+index*2))
			if err != nil || challenge.Status != 200 {
				test.Fatal("challenge failed", err, challenge.Status)
			}
			var bound coldprovision.BoundReply
			var answer map[string]any
			json.Unmarshal(challenge.Body, &bound)
			json.Unmarshal(bound.Response, &answer)
			request := map[string]any{}
			for key, value := range valid {
				request[key] = value
			}
			if name != "other_session_replay" {
				request["challenge"] = answer["challenge"]
				delete(request, "signature")
				if name == "wrong_purpose" {
					raw, err := os.ReadFile(filepath.Join(root, "wrong-purpose.json"))
					if err != nil {
						test.Fatal(err)
					}
					var different map[string]any
					json.Unmarshal(raw, &different)
					request["challenge"] = different["challenge"]
				}
				if name == "other_recipient" {
					request["public_identity"] = negatives["unactivated"]["public_identity"]
				}
				encoded, _ := json.Marshal(request)
				key := ed25519.NewKeyFromSeed(secret[32:])
				request["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(key, append([]byte("family-connect/transport-key-binding/v1\x00"), encoded...)))
				clear(key)
				if name == "wrong_signature" {
					request["signature"] = base64.StdEncoding.EncodeToString(make([]byte, 64))
				}
			}
			reply, err := post(client, coldprovision.Fetch, request, fmt.Sprintf("%032x", 101+index*2))
			if err == nil && !(name == "wrong_signature" && reply.Status == 503) {
				test.Fatalf("unsafe result status=%d", reply.Status)
			}
		})
	}
	test.Run("link_drop_in_flight", func(test *testing.T) {
		client := open()
		defer client.Close()
		result := make(chan error, 1)
		go func() {
			_, err := post(client, coldprovision.Challenge, challengeBody, "33333333333333333333333333333333")
			result <- err
		}()
		select {
		case <-dropSeen:
		case <-ctx.Done():
			test.Fatal("authority request not observed")
		}
		client.Close()
		close(dropRelease)
		select {
		case err := <-result:
			if err == nil {
				test.Fatal("lost response accepted")
			}
		case <-ctx.Done():
			test.Fatal("cancel did not finish")
		}
		if _, err := post(client, coldprovision.Fetch, valid, "33333333333333333333333333333334"); err == nil {
			test.Fatal("closed exchange reused")
		}
	})
	test.Run("bundle_validation", func(test *testing.T) {
		public, err := base64.StdEncoding.DecodeString(valid["public_identity"].(string))
		if err != nil {
			test.Fatal(err)
		}
		if wholedevice.DeliveryValidationCode(bundle, public, anchor, time.Now()) != 0 {
			test.Fatal("valid bundle baseline rejected")
		}
		if wholedevice.DeliveryValidationCode(bundle, public, anchor, time.Now().Add(time.Hour)) == 0 {
			test.Fatal("expired bundle accepted")
		}
		altered := bytes.Replace(bundle, []byte(`"sequence":1`), []byte(`"sequence":0`), 1)
		if bytes.Equal(altered, bundle) {
			altered = append(bytes.Clone(bundle[:len(bundle)-1]), []byte(`,"version":99}`)...)
		}
		if wholedevice.DeliveryValidationCode(altered, public, anchor, time.Now()) == 0 {
			test.Fatal("tampered bundle accepted")
		}
		if wholedevice.DeliveryValidationCode(bundle, make([]byte, 64), anchor, time.Now()) == 0 {
			test.Fatal("other device bundle accepted")
		}
	})
	if after := issued(); after != before {
		test.Fatal("negative requests issued credentials")
	}
}
