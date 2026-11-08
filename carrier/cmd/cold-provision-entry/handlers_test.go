package main

import (
	"context"
	"crypto/ecdh"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func TestExistingAuthorityHandlers(test *testing.T) {
	root, address := os.Getenv("FC_ENTRY_TEST_FIXTURE"), os.Getenv("FC_ENTRY_TEST_BACKEND")
	if root == "" || address == "" {
		test.Skip("requires existing handlers in disposable authority")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	transport := &http.Transport{Proxy: nil, DisableKeepAlives: true}
	defer transport.CloseIdleConnections()
	backend := authorityBackend(roundTrip(func(request *http.Request) (*http.Response, error) {
		if request.URL.Scheme != "https" || request.URL.Host != "185.251.89.19:8443" {
			test.Fatal("incorrect production authority target")
		}
		request = request.Clone(request.Context())
		request.URL.Scheme, request.URL.Host = "http", address
		return transport.RoundTrip(request)
	}))
	load := func(name string) []byte {
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			test.Fatal("disposable input missing")
		}
		return raw
	}
	secret := load("identity.private")
	defer clear(secret)
	key := ed25519.NewKeyFromSeed(secret[32:])
	defer clear(key)
	exchange, _ := ecdh.X25519().NewPrivateKey(secret[:32])
	public := append(exchange.PublicKey().Bytes(), key.Public().(ed25519.PublicKey)...)
	request := map[string]any{"public_identity": base64.StdEncoding.EncodeToString(public), "wireguard_public_key": string(load("wireguard.public"))}
	post := func(path, id string) coldprovision.Reply {
		raw, _ := json.Marshal(request)
		bound, _ := json.Marshal(coldprovision.BoundRequest{Gateway: "nl-amsterdam-1", Request: raw})
		reply, err := backend(ctx, coldprovision.Request{Path: path, ID: id, Body: bound})
		if err != nil {
			test.Fatal("existing handler RPC failed")
		}
		return reply
	}
	challenge := post(coldprovision.Challenge, "00000000000000000000000000000001")
	if challenge.Status != 200 {
		test.Fatal("challenge denied", challenge.Status)
	}
	var envelope coldprovision.BoundReply
	var value map[string]any
	if json.Unmarshal(challenge.Body, &envelope) != nil || json.Unmarshal(envelope.Response, &value) != nil {
		test.Fatal("challenge response malformed")
	}
	request["schema_version"], request["transport"], request["audience"], request["challenge"] = 1, "wireguard", value["audience"], value["challenge"]
	raw, _ := json.Marshal(request)
	request["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(key, append([]byte("family-connect/transport-key-binding/v1\x00"), raw...)))
	reply := post(coldprovision.Fetch, "00000000000000000000000000000002")
	if reply.Status != 200 || json.Unmarshal(reply.Body, &envelope) != nil {
		test.Fatal("readiness issuance failed", reply.Status)
	}
	anchor, _ := base64.StdEncoding.DecodeString(string(load("anchor.pub")))
	if _, _, err := wholedevice.DeliveryMaterial(envelope.Response, secret, anchor, time.Now()); err != nil {
		test.Fatal("existing validator rejected issued bundle")
	}
	request["signature"] = base64.StdEncoding.EncodeToString(make([]byte, 64))
	if post(coldprovision.Fetch, "00000000000000000000000000000003").Status == 200 {
		test.Fatal("invalid identity proof accepted")
	}
}
