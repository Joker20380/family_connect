package qualification

import (
	"bufio"
	"bytes"
	"context"
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/gatewayruntime"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/net/dns/dnsmessage"
)

type nativeConnection struct{ wholedevice.Stream }

func (nativeConnection) LocalAddr() net.Addr              { return &net.TCPAddr{} }
func (nativeConnection) RemoteAddr() net.Addr             { return &net.TCPAddr{} }
func (nativeConnection) SetDeadline(time.Time) error      { return nil }
func (nativeConnection) SetReadDeadline(time.Time) error  { return nil }
func (nativeConnection) SetWriteDeadline(time.Time) error { return nil }

func TestColdProvisionRealAuthorityAndNativeTraffic(test *testing.T) {
	python := os.Getenv("FC_COLD_PROVISION_PYTHON")
	if python == "" {
		test.Skip("requires disposable Friends backend; set FC_COLD_PROVISION_PYTHON")
	}
	repository, _ := filepath.Abs("../../..")
	script := filepath.Join(repository, "tests/fixtures/mobile_bootstrap/provision_backend.py")
	root := test.TempDir()
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, python, script, "serve", root)
	command.Env = append(os.Environ(), "PYTHONPATH="+repository, "PYTHONDONTWRITEBYTECODE=1")
	stdout, err := command.StdoutPipe()
	if err != nil {
		test.Fatal(err)
	}
	command.Stderr = os.Stderr
	if err = command.Start(); err != nil {
		test.Fatal(err)
	}
	defer func() { command.Process.Kill(); command.Wait() }()
	var backendInfo struct{ Address string }
	line, err := bufio.NewReader(stdout).ReadBytes('\n')
	if err != nil || json.Unmarshal(line, &backendInfo) != nil || backendInfo.Address == "" {
		test.Fatal("backend startup", err)
	}
	load := func(name string) []byte {
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			test.Fatal(name, err)
		}
		return raw
	}
	var credentials familysession.Credentials
	if err = json.Unmarshal(load("gateway.json"), &credentials); err != nil {
		test.Fatal(err)
	}
	identity, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil {
		test.Fatal(err)
	}
	anchor, _ := base64.StdEncoding.DecodeString(string(load("anchor.pub")))
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	relayDone := make(chan error, 1)
	go func() { relayDone <- Relay(ctx, listener) }()
	defer func() { cancel(); <-relayDone }()
	provider := Provider{Address: listener.Addr().String()}
	dns, err := net.Listen("tcp", "127.0.0.1:53")
	if err != nil {
		test.Fatal(err)
	}
	defer dns.Close()
	go func() {
		for {
			connection, err := dns.Accept()
			if err != nil {
				return
			}
			connection.SetDeadline(time.Now().Add(time.Second))
			var header [2]byte
			if _, err = io.ReadFull(connection, header[:]); err != nil {
				connection.Close()
				continue
			}
			buffer := make([]byte, binary.BigEndian.Uint16(header[:]))
			if len(buffer) > 4096 {
				connection.Close()
				continue
			}
			if _, err = io.ReadFull(connection, buffer); err != nil {
				connection.Close()
				continue
			}
			var question dnsmessage.Message
			if question.Unpack(buffer) != nil || len(question.Questions) != 1 {
				connection.Close()
				continue
			}
			answer := dnsmessage.Message{Header: dnsmessage.Header{ID: question.ID, Response: true}, Questions: question.Questions}
			if question.Questions[0].Type == dnsmessage.TypeA {
				answer.Answers = []dnsmessage.Resource{{Header: dnsmessage.ResourceHeader{Name: question.Questions[0].Name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET, TTL: 10}, Body: &dnsmessage.AResource{A: [4]byte{93, 184, 215, 14}}}}
			}
			raw, _ := answer.Pack()
			binary.BigEndian.PutUint16(header[:], uint16(len(raw)))
			connection.Write(append(header[:], raw...))
			connection.Close()
		}
	}()
	backend, err := coldprovision.LoopbackBackend(backendInfo.Address)
	if err != nil {
		test.Fatal(err)
	}
	dropSeen, dropRelease := make(chan struct{}), make(chan struct{})
	authorityBackend := backend
	backend = func(ctx context.Context, request coldprovision.Request) (coldprovision.Reply, error) {
		reply, err := authorityBackend(ctx, request)
		if request.ID == "33333333333333333333333333333333" && request.Path == coldprovision.Challenge {
			close(dropSeen)
			select {
			case <-dropRelease:
			case <-ctx.Done():
				return coldprovision.Reply{}, ctx.Err()
			}
		}
		return reply, err
	}
	publicationFailure := make(chan error, 1)
	publish := func(directory bootstrap.Directory) ([]byte, error) {
		raw, _ := json.Marshal(directory)
		if err := os.WriteFile(filepath.Join(root, "provision-seed.json"), raw, 0600); err != nil {
			return nil, err
		}
		issuer := exec.CommandContext(ctx, python, script, "issue", root)
		issuer.Env = command.Env
		issuer.Stderr = os.Stderr
		err := issuer.Run()
		if err != nil {
			publicationFailure <- err
		}
		if err != nil {
			return nil, err
		}
		return os.ReadFile(filepath.Join(root, "locator.json"))
	}
	provisionDone := make(chan error, 1)
	go func() {
		provisionDone <- coldprovision.Run(ctx, coldprovision.Config{Anchor: anchor, Node: "nl-amsterdam-1", Family: credentials.Family, Gateway: credentials.Gateway, Lifetime: 2 * time.Minute, Identity: identity, Publish: publish}, provider, provider.Seed, backend)
	}()
	defer func() { cancel(); <-provisionDone }()
	await := func(name string) []byte {
		for {
			select {
			case err := <-publicationFailure:
				test.Fatal("locator publication", err)
			default:
			}
			raw, err := os.ReadFile(filepath.Join(root, name))
			if err == nil {
				return raw
			}
			if ctx.Err() != nil {
				test.Fatal("publication timeout", name)
			}
			time.Sleep(10 * time.Millisecond)
		}
	}
	locator := await("locator.json")
	test.Log("locator issued by existing authority after SeedManager publication, before client Connect")
	origin := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Write([]byte("verified provisioning traffic"))
	}))
	defer origin.Close()
	echo, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	defer echo.Close()
	go func() {
		for {
			connection, err := echo.Accept()
			if err != nil {
				return
			}
			go func() { defer connection.Close(); io.Copy(connection, connection) }()
		}
	}()
	services := map[string]netip.AddrPort{"chat-mailbox.family-connect.invalid": echo.Addr().(*net.TCPAddr).AddrPort(), "chat-api.family-connect.invalid": origin.Listener.Addr().(*net.TCPAddr).AddrPort()}
	starter := roombroker.PacketGateway{TelemostGateway: roombroker.TelemostGateway{CredentialsPath: filepath.Join(root, "gateway.json"), Services: services, AllowInternet: true}, Connect: provider.Gateway, DNSUpstream: dns.Addr().String()}
	gatewayDone := make(chan error, 1)
	go func() {
		gatewayDone <- gatewayruntime.Run(ctx, gatewayruntime.Config{Profile: filepath.Join(root, "gateway.json"), Directory: filepath.Join(root, "directory.json"), Listen: "127.0.0.1:0", Duration: time.Minute}, provider, provider.Seed, starter)
	}()
	defer func() { cancel(); <-gatewayDone }()
	await("directory.json")
	for _, invalid := range [][]byte{nil, []byte(`{}`), bytes.Replace(locator, []byte(`"version":1`), []byte(`"version":2`), 1)} {
		if _, _, err := coldprovision.Verify(invalid, anchor, "nl-amsterdam-1", time.Now()); err == nil {
			test.Fatal("invalid locator accepted")
		}
	}
	var forged coldprovision.Locator
	json.Unmarshal(locator, &forged)
	forged.Signature = base64.StdEncoding.EncodeToString(make([]byte, 64))
	forgedRaw, _ := json.Marshal(forged)
	if _, _, err := coldprovision.Verify(forgedRaw, anchor, "nl-amsterdam-1", time.Now()); err == nil {
		test.Fatal("forged locator accepted")
	}
	if _, _, err := coldprovision.Verify(locator, anchor, "nl-amsterdam-2", time.Now()); err == nil {
		test.Fatal("wrong node locator")
	}
	if _, _, err := coldprovision.Verify(locator, anchor, "nl-amsterdam-1", time.Now().Add(3*time.Minute)); err == nil {
		test.Fatal("expired locator")
	}
	client, err := coldprovision.Open(ctx, locator, anchor, "nl-amsterdam-1", provider.Seed)
	if err != nil {
		test.Fatal("cold Open", err)
	}
	defer client.Close()
	if _, err := client.Post("/friends/activate", []byte(`{}`), "00000000000000000000000000000001"); err == nil {
		test.Fatal("activation exposed")
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
		reply, err := client.Post(path, bound, id)
		if err != nil {
			test.Fatal("provisioning request", path, err)
		}
		return reply
	}
	challenge := post(coldprovision.Challenge, "00000000000000000000000000000001")
	if challenge.Status != 200 {
		test.Fatal("challenge status", challenge.Status)
	}
	var envelope coldprovision.BoundReply
	var value map[string]any
	json.Unmarshal(challenge.Body, &envelope)
	json.Unmarshal(envelope.Response, &value)
	request["schema_version"], request["transport"], request["audience"], request["challenge"] = 1, "wireguard", value["audience"], value["challenge"]
	raw, _ := json.Marshal(request)
	request["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(key, append([]byte("family-connect/transport-key-binding/v1\x00"), raw...)))
	reply := post(coldprovision.Fetch, "00000000000000000000000000000002")
	if reply.Status != 200 {
		test.Fatal("readiness status", reply.Status)
	}
	json.Unmarshal(reply.Body, &envelope)
	profile, directory, err := wholedevice.DeliveryMaterial(envelope.Response, secret, anchor, time.Now())
	if err != nil {
		test.Fatal("unchanged native validator", err)
	}
	defer clear(profile)
	test.Log("server TLS, registered-device proof and actual backend signed delivery accepted")
	if _, err := client.Post(coldprovision.Fetch, []byte(`{}`), "00000000000000000000000000000003"); err == nil {
		test.Fatal("replay after fetch")
	}
	provisioningNegatives(test, ctx, root, provider, locator, anchor, secret, envelope.Response, request, dropSeen, dropRelease)
	network, err := underlay.New(ctx, "127.0.0.1:53", func(int) bool { return true })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	physical := Provider{Address: provider.Address, DialContext: network.DialContext}
	session, err := wholedevice.OpenProvisionedWithTransport(ctx, profile, directory, network, func(string) {}, wholedevice.PacketTransport{Seed: physical.Seed, Dedicated: physical.Gateway})
	if err != nil {
		test.Fatal("ordinary native MESH", err)
	}
	defer session.Close()
	stream, err := session.OpenService(ctx, "chat-mailbox")
	if err != nil {
		test.Fatal(err)
	}
	if _, err = stream.Write([]byte("cold-start-bytes")); err != nil {
		test.Fatal(err)
	}
	result := make([]byte, len("cold-start-bytes"))
	if _, err = io.ReadFull(stream, result); err != nil || string(result) != "cold-start-bytes" {
		test.Fatal("TCP", err)
	}
	stream.Close()
	secure, err := session.OpenService(ctx, "chat-api")
	if err != nil {
		test.Fatal(err)
	}
	defer secure.Reset()
	roots := x509.NewCertPool()
	roots.AddCert(origin.Certificate())
	secured := tls.Client(nativeConnection{secure}, &tls.Config{RootCAs: roots, ServerName: "example.com", MinVersion: tls.VersionTLS13})
	if err = secured.HandshakeContext(ctx); err != nil {
		test.Fatal("verified HTTPS", err)
	}
	io.WriteString(secured, "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
	response, err := http.ReadResponse(bufio.NewReader(secured), nil)
	if err != nil {
		test.Fatal(err)
	}
	contents, err := io.ReadAll(response.Body)
	response.Body.Close()
	if err != nil || string(contents) != "verified provisioning traffic" {
		test.Fatal("HTTPS bytes", err)
	}
	name, _ := dnsmessage.NewName("example.com.")
	query, _ := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 91}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
	answers := make(chan []byte, 1)
	session.HandleDNSDatagram(query, "10.79.0.1", 53, func(raw []byte) error { answers <- raw; return nil })
	select {
	case raw := <-answers:
		var answer dnsmessage.Message
		if answer.Unpack(raw) != nil || !answer.Response || answer.ID != 91 || len(answer.Answers) == 0 {
			test.Fatal("DNS response")
		}
	case <-ctx.Done():
		test.Fatal("DNS timeout")
	}
	session.Close()
	if !session.Failed() {
		test.Fatal("native cleanup")
	}
	test.Log("ordinary native Family TLS/mux: new TCP, DNS, verified HTTPS, cleanup PASS; Android owner/vault not covered by this test")
	androidSourcePipeline(test, ctx, root, provider, origin, network)
}
