package desktopmesh

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/netip"
	"regexp"
	"strings"
)

const MaxNormalResponse = 65536
const MaxNormalSequence = 1<<53 - 1

type NormalConfiguration struct {
	Response json.RawMessage
	Catalog  json.RawMessage
	Sequence uint64
	Digest   string
}

func (NormalConfiguration) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[normal configuration redacted]")
}

func (configuration *NormalConfiguration) Clear() {
	clear(configuration.Response)
	clear(configuration.Catalog)
	configuration.Response, configuration.Catalog = nil, nil
}

func normalObject(raw []byte, limit int, fields string) (map[string]json.RawMessage, error) {
	var value map[string]json.RawMessage
	if strictReadinessJSON(raw, limit, &value) != nil || len(value) != len(strings.Fields(fields)) {
		return nil, ErrConfiguration
	}
	for _, name := range strings.Fields(fields) {
		field, exists := value[name]
		if !exists || bytes.Equal(bytes.TrimSpace(field), []byte("null")) {
			return nil, ErrConfiguration
		}
	}
	return value, nil
}

func normalText(raw json.RawMessage) (string, error) {
	var value string
	if json.Unmarshal(raw, &value) != nil {
		return "", ErrConfiguration
	}
	return value, nil
}

func normalBase64(raw json.RawMessage, size int) ([]byte, error) {
	text, err := normalText(raw)
	if err != nil {
		return nil, err
	}
	value, err := base64.StdEncoding.DecodeString(text)
	if err != nil || len(value) != size || base64.StdEncoding.EncodeToString(value) != text {
		return nil, ErrConfiguration
	}
	return value, nil
}

func NormalCatalogFloor(raw, anchor []byte) (uint64, string, error) {
	if len(anchor) != ed25519.PublicKeySize {
		return 0, "", ErrConfiguration
	}
	envelope, err := normalObject(raw, 16384, "payload signature")
	if err != nil {
		return 0, "", err
	}
	text, err := normalText(envelope["payload"])
	if err != nil {
		return 0, "", err
	}
	payload, err := base64.StdEncoding.DecodeString(text)
	if err != nil || len(payload) == 0 || len(payload) > 8192 || base64.StdEncoding.EncodeToString(payload) != text {
		return 0, "", ErrConfiguration
	}
	signature, err := normalBase64(envelope["signature"], ed25519.SignatureSize)
	if err != nil || !ed25519.Verify(anchor, append([]byte("family-connect/invited-test/v1\x00"), payload...), signature) {
		return 0, "", ErrConfiguration
	}
	value, err := normalObject(payload, 8192, "schema sequence access gateways")
	var schema int
	var sequence uint64
	var access string
	var gateways []json.RawMessage
	if err != nil || json.Unmarshal(value["schema"], &schema) != nil || schema != 2 ||
		json.Unmarshal(value["sequence"], &sequence) != nil || sequence == 0 || sequence > MaxNormalSequence ||
		json.Unmarshal(value["access"], &access) != nil || access != "invite-test" ||
		json.Unmarshal(value["gateways"], &gateways) != nil || len(gateways) != 2 {
		return 0, "", ErrConfiguration
	}
	seen := map[string]bool{}
	for _, rawGateway := range gateways {
		gateway, err := normalObject(rawGateway, 8192, "country tcp awg")
		if err != nil {
			return 0, "", err
		}
		country, err := normalText(gateway["country"])
		if err != nil || (country != "ru" && country != "nl") || seen[country] {
			return 0, "", ErrConfiguration
		}
		seen[country] = true
		tcp, err := normalObject(gateway["tcp"], 4096, "type server port id public_key server_name short_id")
		if err != nil {
			return 0, "", err
		}
		credential, err := normalText(tcp["id"])
		if err != nil || credential != "DEVICE_CREDENTIAL" {
			return 0, "", ErrConfiguration
		}
		awg, err := normalText(gateway["awg"])
		if err != nil || len(awg) > 8192 || strings.Count(awg, "LOCAL_DEVICE_KEY") != 1 ||
			strings.Count(awg, "ASSIGNED_ADDRESS") != 1 ||
			!regexp.MustCompile(`(?m)^PrivateKey = LOCAL_DEVICE_KEY$`).MatchString(awg) ||
			!regexp.MustCompile(`(?m)^Address = ASSIGNED_ADDRESS$`).MatchString(awg) {
			return 0, "", ErrConfiguration
		}
	}
	digest := sha256.Sum256(payload)
	return sequence, hex.EncodeToString(digest[:]), nil
}

func VerifyNormalResponse(raw, anchor []byte, device, country string, floors []json.RawMessage) (NormalConfiguration, error) {
	if (country != "ru" && country != "nl") || !regexp.MustCompile(`^[0-9a-f]{32}$`).MatchString(device) || len(floors) > 3 {
		return NormalConfiguration{}, ErrConfiguration
	}
	floor, previous, err := VerifyNormalFloors(floors, anchor)
	if err != nil {
		return NormalConfiguration{}, err
	}
	value, err := normalObject(raw, MaxNormalResponse, "device country address tcp_id catalog")
	if err != nil {
		return NormalConfiguration{}, err
	}
	actualDevice, deviceErr := normalText(value["device"])
	actualCountry, countryErr := normalText(value["country"])
	address, addressErr := normalText(value["address"])
	credential, credentialErr := normalText(value["tcp_id"])
	if deviceErr != nil || countryErr != nil || addressErr != nil || credentialErr != nil ||
		actualDevice != device || actualCountry != country ||
		!regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`).MatchString(credential) ||
		strings.ReplaceAll(credential, "-", "") == strings.Repeat("0", 32) {
		return NormalConfiguration{}, ErrConfiguration
	}
	prefix, err := netip.ParsePrefix(address)
	region := netip.MustParsePrefix("10.83.0.0/16")
	if country == "ru" {
		region = netip.MustParsePrefix("10.84.0.0/16")
	}
	if err != nil || prefix.String() != address || prefix.Bits() != 32 || !region.Contains(prefix.Addr()) {
		return NormalConfiguration{}, ErrConfiguration
	}
	octets := prefix.Addr().As4()
	if (octets[2] == 0 && octets[3] <= 1) || (octets[2] == 255 && octets[3] == 255) {
		return NormalConfiguration{}, ErrConfiguration
	}
	sequence, digest, err := NormalCatalogFloor(value["catalog"], anchor)
	if err != nil || sequence < floor || (sequence == floor && previous != digest) {
		return NormalConfiguration{}, ErrConfiguration
	}
	return NormalConfiguration{Response: bytes.Clone(raw), Catalog: bytes.Clone(value["catalog"]), Sequence: sequence, Digest: digest}, nil
}

type normalChallengeTransport struct{ ReadinessTransport }

func VerifyNormalFloors(floors []json.RawMessage, anchor []byte) (uint64, string, error) {
	var floor uint64
	previous := ""
	for _, catalog := range floors {
		sequence, digest, err := NormalCatalogFloor(catalog, anchor)
		if err != nil || (sequence == floor && digest != previous) {
			return 0, "", ErrConfiguration
		}
		if sequence > floor {
			floor, previous = sequence, digest
		}
	}
	return floor, previous, nil
}

func (transport normalChallengeTransport) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	raw, err := transport.ReadinessTransport.Post(ctx, path, body, probe)
	if err == nil {
		_, err = normalObject(raw, 16384, "challenge expires_at audience")
	}
	if err != nil {
		clear(raw)
		return nil, err
	}
	return raw, nil
}

func (client *ReadinessClient) FetchNormal(ctx context.Context, transport ReadinessTransport, country string, anchor []byte, floors []json.RawMessage) (NormalConfiguration, error) {
	if transport == nil || (country != "ru" && country != "nl") || len(anchor) != 32 || len(floors) > 3 {
		return NormalConfiguration{}, ErrConfiguration
	}
	if _, _, err := VerifyNormalFloors(floors, anchor); err != nil {
		return NormalConfiguration{}, err
	}
	if err := ctx.Err(); err != nil {
		return NormalConfiguration{}, err
	}
	client.mu.Lock()
	closed := len(client.signing) != ed25519.PrivateKeySize
	client.mu.Unlock()
	if closed {
		return NormalConfiguration{}, ErrClosed
	}
	attempt, err := NewReadinessAttempt()
	if err != nil {
		return NormalConfiguration{}, err
	}
	body, err := json.Marshal(map[string]string{"public_identity": base64.StdEncoding.EncodeToString(client.public),
		"wireguard_public_key": base64.StdEncoding.EncodeToString(client.wireguard), "purpose": country, "invitation": ""})
	if err != nil {
		return NormalConfiguration{}, ErrConfiguration
	}
	defer clear(body)
	nonce, err := client.challenge(ctx, normalChallengeTransport{transport}, "/friends/challenge", body, attempt.ChallengeID)
	if err != nil {
		return NormalConfiguration{}, err
	}
	proof, err := client.proof(nonce)
	if err != nil {
		return NormalConfiguration{}, err
	}
	defer clear(proof)
	raw, err := transport.Post(ctx, "/friends/configuration/"+country, proof, attempt.FetchID)
	defer clear(raw)
	if ctx.Err() != nil {
		return NormalConfiguration{}, ctx.Err()
	}
	if err != nil {
		return NormalConfiguration{}, err
	}
	return VerifyNormalResponse(raw, anchor, client.Reference(), country, floors)
}
