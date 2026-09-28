package roombroker

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func LoadCredentials(path string) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || info.Size() > 48<<10 {
		return nil, Code("credentials_rejected")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, Code("credentials_rejected")
	}
	return raw, nil
}

func ServerTLS(path string) (*tls.Config, error) {
	raw, err := LoadCredentials(path)
	if err != nil {
		return nil, err
	}
	defer clear(raw)
	config, _, err := familysession.Configuration(raw, true)
	if err != nil {
		return nil, Code("credentials_rejected")
	}
	controlALPN(config)
	config.GetConfigForClient = func(*tls.ClientHelloInfo) (*tls.Config, error) {
		raw, err := LoadCredentials(path)
		if err != nil {
			return nil, err
		}
		defer clear(raw)
		fresh, _, err := familysession.Configuration(raw, true)
		if err == nil {
			controlALPN(fresh)
		}
		return fresh, err
	}
	return config, nil
}

func controlALPN(config *tls.Config) {
	verify := config.VerifyConnection
	config.NextProtos = []string{"http/1.1"}
	config.VerifyConnection = func(state tls.ConnectionState) error {
		if state.NegotiatedProtocol != "http/1.1" {
			return Code("control_protocol_rejected")
		}
		state.NegotiatedProtocol = familysession.Protocol
		return verify(state)
	}
}

func RequestAuthorizer(path string, state *tls.ConnectionState) Authorize {
	return func(ctx context.Context) (Identity, error) {
		if state == nil || len(state.PeerCertificates) != 1 || ctx.Err() != nil {
			return Identity{}, Code("unauthorized")
		}
		raw, err := LoadCredentials(path)
		if err != nil {
			return Identity{}, err
		}
		defer clear(raw)
		config, _, err := familysession.Configuration(raw, true)
		if err != nil {
			return Identity{}, Code("unauthorized")
		}
		controlALPN(config)
		peer := state.PeerCertificates[0]
		if _, err := peer.Verify(x509.VerifyOptions{Roots: config.ClientCAs, KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}}); err != nil {
			return Identity{}, Code("unauthorized")
		}
		if config.VerifyConnection(*state) != nil {
			return Identity{}, Code("unauthorized")
		}
		var credentials familysession.Credentials
		if json.Unmarshal(raw, &credentials) != nil {
			return Identity{}, Code("unauthorized")
		}
		identity := Identity{Family: credentials.Family, Device: peer.Subject.SerialNumber}
		key, ok := peer.PublicKey.(ed25519.PublicKey)
		if !ok {
			return Identity{}, Code("unauthorized")
		}
		copy(identity.PublicKey[:], key)
		return identity, nil
	}
}

func (broker *Broker) Handler(path string) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Cache-Control", "no-store")
		writer.Header().Set("Content-Type", "application/json")
		writer.Header().Set("X-Content-Type-Options", "nosniff")
		fail := func(code Code, status int) {
			writer.WriteHeader(status)
			_ = json.NewEncoder(writer).Encode(map[string]Code{"code": code})
		}
		if request.Method != http.MethodPost || request.URL.RawQuery != "" || request.Header.Get("Content-Type") != "application/json" {
			fail("invalid_request", 400)
			return
		}
		authorize := RequestAuthorizer(path, request.TLS)
		if _, err := authorized(request.Context(), authorize); err != nil {
			fail("unauthorized", 403)
			return
		}
		var input struct {
			SetupID string `json:"setup_id"`
		}
		decoder := json.NewDecoder(http.MaxBytesReader(writer, request.Body, 256))
		decoder.DisallowUnknownFields()
		if decoder.Decode(&input) != nil || decoder.Decode(new(any)) != io.EOF {
			fail("invalid_request", 400)
			return
		}
		var result any = struct{}{}
		var err error
		switch request.URL.Path {
		case "/v1/rooms/challenge":
			if input.SetupID != "" {
				fail("invalid_request", 400)
				return
			}
			var id string
			id, err = broker.Challenge(request.Context(), authorize)
			result = map[string]string{"setup_id": id}
		case "/v1/rooms/create":
			result, err = broker.Create(request.Context(), input.SetupID, authorize)
		case "/v1/rooms/claim":
			err = broker.Claim(request.Context(), input.SetupID, authorize)
		case "/v1/rooms/cancel":
			err = broker.Cancel(request.Context(), input.SetupID, authorize)
		default:
			fail("not_found", 404)
			return
		}
		if err != nil {
			code, ok := err.(Code)
			if !ok {
				code = "unavailable"
			}
			fail(code, 409)
			return
		}
		if err := json.NewEncoder(writer).Encode(result); err != nil && input.SetupID != "" {
			_ = broker.Cancel(context.Background(), input.SetupID, authorize)
		}
	})
}

type Client struct {
	base   string
	client *http.Client
}

func NewClient(base string, raw []byte) (*Client, error) {
	if !strings.HasPrefix(base, "https://") || strings.ContainsAny(base, "?#@\r\n") {
		return nil, Code("invalid_endpoint")
	}
	config, _, err := familysession.Configuration(raw, false)
	if err != nil {
		return nil, Code("credentials_rejected")
	}
	controlALPN(config)
	transport := &http.Transport{TLSClientConfig: config, TLSHandshakeTimeout: 10 * time.Second, DisableKeepAlives: true}
	return &Client{strings.TrimRight(base, "/"), &http.Client{Transport: transport, Timeout: 65 * time.Second,
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}}, nil
}

func (client *Client) call(ctx context.Context, action, id string, result any) error {
	raw, _ := json.Marshal(map[string]string{"setup_id": id})
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, client.base+"/v1/rooms/"+action, bytes.NewReader(raw))
	if err != nil {
		return Code("control_request")
	}
	request.Header.Set("Content-Type", "application/json")
	response, err := client.client.Do(request)
	if err != nil {
		return Code("control_unavailable")
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		return Code("control_rejected")
	}
	raw, err = io.ReadAll(io.LimitReader(response.Body, 4097))
	if err != nil || len(raw) > 4096 || json.Unmarshal(raw, result) != nil {
		return Code("control_response")
	}
	return nil
}

func (client *Client) Create(ctx context.Context) (Descriptor, error) {
	var challenge struct {
		SetupID string `json:"setup_id"`
	}
	if err := client.call(ctx, "challenge", "", &challenge); err != nil {
		return Descriptor{}, err
	}
	if len(challenge.SetupID) != 64 {
		return Descriptor{}, Code("control_response")
	}
	var descriptor Descriptor
	err := client.call(ctx, "create", challenge.SetupID, &descriptor)
	if err == nil && (descriptor.Transport != "telemost-webrtc" || descriptor.SetupID != challenge.SetupID ||
		!ValidJoinURL(descriptor.JoinURL) || !time.Now().Before(descriptor.ExpiresAt) || time.Until(descriptor.ExpiresAt) > 2*time.Minute) {
		err = Code("control_response")
	}
	if err == nil {
		err = client.call(ctx, "claim", descriptor.SetupID, &struct{}{})
	}
	if err != nil {
		client.Cancel(challenge.SetupID)
		return Descriptor{}, err
	}
	return descriptor, nil
}

func (client *Client) Cancel(id string) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	_ = client.call(ctx, "cancel", id, &struct{}{})
}
