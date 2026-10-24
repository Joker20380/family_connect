package desktopmesh

import (
	"bytes"
	"context"
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type ReadinessTransport interface {
	Post(context.Context, string, []byte, string) ([]byte, error)
}

func NewReadinessAttempt() (ReadinessAttempt, error) {
	var material [32]byte
	if _, err := rand.Read(material[:]); err != nil {
		return ReadinessAttempt{}, ErrConfiguration
	}
	attempt := ReadinessAttempt{ChallengeID: hex.EncodeToString(material[:16]), FetchID: hex.EncodeToString(material[16:])}
	if !attempt.Valid() {
		return ReadinessAttempt{}, ErrConfiguration
	}
	return attempt, nil
}

type ReadinessFailure struct {
	Code          string
	Availability  bool
	Authorization bool
	Network       bool
}

func (failure *ReadinessFailure) Error() string { return failure.Code }

type ReadinessClient struct {
	mu        sync.Mutex
	signing   ed25519.PrivateKey
	public    []byte
	wireguard []byte
	clock     func() time.Time
}

func (*ReadinessClient) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[readiness client redacted]")
}

func NewReadinessClient(identity, wireguardPublic []byte) (*ReadinessClient, error) {
	if len(identity) != 64 || len(wireguardPublic) != 32 {
		return nil, ErrConfiguration
	}
	exchange, err := ecdh.X25519().NewPrivateKey(identity[:32])
	if err != nil {
		return nil, ErrConfiguration
	}
	signing := ed25519.NewKeyFromSeed(identity[32:])
	public := append(exchange.PublicKey().Bytes(), signing.Public().(ed25519.PublicKey)...)
	return &ReadinessClient{signing: signing, public: public, wireguard: bytes.Clone(wireguardPublic), clock: time.Now}, nil
}

func (client *ReadinessClient) Close() {
	client.mu.Lock()
	defer client.mu.Unlock()
	clear(client.signing)
	client.signing = nil
}

func (client *ReadinessClient) Public() []byte { return bytes.Clone(client.public) }

func (client *ReadinessClient) Reference() string {
	digest := sha256.Sum256(client.public)
	return hex.EncodeToString(digest[:16])
}

func (client *ReadinessClient) challengeBody() ([]byte, error) {
	return json.Marshal(struct {
		Public    string `json:"public_identity"`
		Wireguard string `json:"wireguard_public_key"`
	}{base64.StdEncoding.EncodeToString(client.public), base64.StdEncoding.EncodeToString(client.wireguard)})
}

func (client *ReadinessClient) proof(nonce string) ([]byte, error) {
	client.mu.Lock()
	defer client.mu.Unlock()
	decoded, err := base64.StdEncoding.DecodeString(nonce)
	if len(client.signing) != ed25519.PrivateKeySize || err != nil || len(decoded) != 32 || base64.StdEncoding.EncodeToString(decoded) != nonce {
		return nil, ErrConfiguration
	}
	binding := map[string]any{"schema_version": 1, "public_identity": base64.StdEncoding.EncodeToString(client.public),
		"wireguard_public_key": base64.StdEncoding.EncodeToString(client.wireguard), "challenge": nonce,
		"audience": "family-connect/enrollment/v1", "transport": "wireguard"}
	raw, err := json.Marshal(binding)
	if err != nil {
		return nil, ErrConfiguration
	}
	message := append([]byte("family-connect/transport-key-binding/v1\x00"), raw...)
	defer clear(message)
	binding["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(client.signing, message))
	return json.Marshal(binding)
}

func (client *ReadinessClient) challenge(ctx context.Context, transport ReadinessTransport, path string, body []byte, probe string) (string, error) {
	raw, err := transport.Post(ctx, path, body, probe)
	defer clear(raw)
	if ctx.Err() != nil {
		return "", ctx.Err()
	}
	if err != nil {
		return "", err
	}
	var reply struct {
		Challenge string `json:"challenge"`
		Expires   int64  `json:"expires_at"`
		Audience  string `json:"audience"`
	}
	now := client.clock().Unix()
	if strictReadinessJSON(raw, 16384, &reply) != nil || reply.Expires <= now || reply.Expires-now > 120 || reply.Audience != "family-connect/enrollment/v1" {
		return "", &ReadinessFailure{Code: "CHALLENGE_INCOMPATIBLE_RESPONSE"}
	}
	nonce, err := base64.StdEncoding.DecodeString(reply.Challenge)
	if err != nil || len(nonce) != 32 || base64.StdEncoding.EncodeToString(nonce) != reply.Challenge {
		return "", &ReadinessFailure{Code: "CHALLENGE_INCOMPATIBLE_RESPONSE"}
	}
	return reply.Challenge, nil
}

func (client *ReadinessClient) Fetch(ctx context.Context, transport ReadinessTransport, attempt ReadinessAttempt) ([]byte, error) {
	if transport == nil || !attempt.Valid() {
		return nil, ErrConfiguration
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	client.mu.Lock()
	closed := len(client.signing) != ed25519.PrivateKeySize
	client.mu.Unlock()
	if closed {
		return nil, ErrClosed
	}
	body, err := client.challengeBody()
	if err != nil {
		return nil, err
	}
	defer clear(body)
	nonce, err := client.challenge(ctx, transport, "/friends/restricted-readiness/challenge", body, attempt.ChallengeID)
	if err != nil {
		return nil, err
	}
	proof, err := client.proof(nonce)
	if err != nil {
		return nil, err
	}
	defer clear(proof)
	raw, err := transport.Post(ctx, "/friends/restricted-readiness", proof, attempt.FetchID)
	if ctx.Err() != nil {
		clear(raw)
		return nil, ctx.Err()
	}
	if err != nil {
		clear(raw)
		return nil, err
	}
	var response wholedevice.ReadinessDelivery
	if strictReadinessJSON(raw, wholedevice.MaxReadiness, &response) != nil || response.Challenge != nonce || response.Device != client.Reference() {
		clear(raw)
		return nil, &ReadinessFailure{Code: "FETCH_INCOMPATIBLE_RESPONSE"}
	}
	return raw, nil
}

type ReadinessSource string

const (
	ReadinessFresh ReadinessSource = "FRESH"
	ReadinessSaved ReadinessSource = "VALIDATED_CACHE"
)

func ResolveReadiness(ctx context.Context, cache *ReadinessCache, client *ReadinessClient, transport ReadinessTransport, attempt ReadinessAttempt, required bool) ([]byte, ReadinessSource, error) {
	raw, source, _, err := ResolveReadinessWithResult(ctx, cache, client, transport, attempt, required)
	return raw, source, err
}

func ResolveReadinessWithResult(ctx context.Context, cache *ReadinessCache, client *ReadinessClient, transport ReadinessTransport, attempt ReadinessAttempt, required bool) (raw []byte, source ReadinessSource, result ReadinessCode, err error) {
	raw, source, err = resolveReadiness(ctx, cache, client, transport, attempt, required, &result)
	return
}

func resolveReadiness(ctx context.Context, cache *ReadinessCache, client *ReadinessClient, transport ReadinessTransport, attempt ReadinessAttempt, required bool, result *ReadinessCode) ([]byte, ReadinessSource, error) {
	if cache == nil || client == nil || transport == nil || !attempt.Valid() {
		return nil, "", ErrConfiguration
	}
	if ctx.Err() != nil {
		return nil, "", ctx.Err()
	}
	run, err := cache.Attempt(client.clock(), required)
	if err != nil {
		return nil, "", err
	}
	if run {
		*result = "FETCH_FAILED"
		raw, err := client.Fetch(ctx, transport, attempt)
		if err == nil {
			if ctx.Err() != nil {
				clear(raw)
				return nil, "", ctx.Err()
			}
			err = cache.Accept(raw, attempt, client.clock())
			clear(raw)
			if ctx.Err() != nil {
				return nil, "", ctx.Err()
			}
			if err != nil {
				*result = ReadinessPersistence
				var code ReadinessCode
				if errors.As(err, &code) {
					*result = code
				}
				return nil, "", err
			}
			usable, code := cache.Usable(client.clock())
			if ctx.Err() != nil {
				clear(usable)
				return nil, "", ctx.Err()
			}
			if code != ReadinessReady {
				*result = code
				return nil, "", code
			}
			*result = ReadinessReady
			return usable, ReadinessFresh, nil
		}
		if ctx.Err() != nil {
			return nil, "", ctx.Err()
		}
		var failure *ReadinessFailure
		if !errors.As(err, &failure) {
			return nil, "", err
		}
		if failure.Authorization {
			*result = ReadinessDenied
			if err := cache.Deny(); err != nil {
				*result = ReadinessPersistence
				return nil, "", err
			}
			return nil, "", ReadinessDenied
		}
		if !failure.Availability {
			return nil, "", err
		}
	}
	raw, code := cache.Usable(client.clock())
	if ctx.Err() != nil {
		clear(raw)
		return nil, "", ctx.Err()
	}
	if code != ReadinessReady {
		return nil, "", code
	}
	return raw, ReadinessSaved, nil
}
