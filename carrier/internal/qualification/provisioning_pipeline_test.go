package qualification

import (
	"bufio"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/net/dns/dnsmessage"
)

func pipelineTraffic(ctx context.Context, session *wholedevice.Session, origin *httptest.Server) error {
	stream, err := session.OpenService(ctx, "chat-mailbox")
	if err != nil {
		return err
	}
	defer stream.Reset()
	if _, err = stream.Write([]byte("cold-java-native")); err != nil {
		return err
	}
	raw := make([]byte, len("cold-java-native"))
	if _, err = io.ReadFull(stream, raw); err != nil || string(raw) != "cold-java-native" {
		return fmt.Errorf("TCP verification")
	}
	secure, err := session.OpenService(ctx, "chat-api")
	if err != nil {
		return err
	}
	defer secure.Reset()
	roots := x509.NewCertPool()
	roots.AddCert(origin.Certificate())
	connection := tls.Client(nativeConnection{secure}, &tls.Config{RootCAs: roots, ServerName: "example.com", MinVersion: tls.VersionTLS13})
	if err = connection.HandshakeContext(ctx); err != nil {
		return err
	}
	io.WriteString(connection, "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n")
	response, err := http.ReadResponse(bufio.NewReader(connection), nil)
	if err != nil {
		return err
	}
	body, err := io.ReadAll(response.Body)
	response.Body.Close()
	if err != nil || string(body) != "verified provisioning traffic" {
		return fmt.Errorf("HTTPS verification")
	}
	name, _ := dnsmessage.NewName("example.com.")
	query, _ := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 92}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
	answers := make(chan []byte, 1)
	session.HandleDNSDatagram(query, "10.79.0.1", 53, func(raw []byte) error { answers <- raw; return nil })
	select {
	case raw := <-answers:
		var answer dnsmessage.Message
		if answer.Unpack(raw) != nil || !answer.Response || answer.ID != 92 || len(answer.Answers) == 0 {
			return fmt.Errorf("DNS verification")
		}
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func androidSourcePipeline(test *testing.T, ctx context.Context, root string, provider Provider, origin *httptest.Server, network *underlay.Network) {
	java, classpath := os.Getenv("FC_COLD_JAVA"), os.Getenv("FC_COLD_CLASSPATH")
	if java == "" || classpath == "" {
		test.Log("Android source pipeline NOT_RUN: JVM fixture paths absent")
		return
	}
	assets := filepath.Join(root, "client-assets")
	clientState := filepath.Join(root, "client-state")
	if err := os.MkdirAll(filepath.Join(assets, "provisioning"), 0700); err != nil {
		test.Fatal(err)
	}
	for source, destination := range map[string]string{"locator.json": "provisioning/nl-amsterdam-1.json", "anchor.pub": "anchor.pub"} {
		raw, err := os.ReadFile(filepath.Join(root, source))
		if err != nil {
			test.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(assets, destination), raw, 0600); err != nil {
			test.Fatal(err)
		}
	}
	var mu sync.Mutex
	var cold *coldprovision.Client
	var session *wholedevice.Session
	phase := -1
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		mu.Lock()
		defer mu.Unlock()
		var value map[string]json.RawMessage
		if json.NewDecoder(io.LimitReader(request.Body, 200000)).Decode(&value) != nil {
			writer.WriteHeader(400)
			return
		}
		text := func(key string) string { var result string; json.Unmarshal(value[key], &result); return result }
		data := func(key string) []byte { raw, _ := base64.StdEncoding.DecodeString(text(key)); return raw }
		result := map[string]any{}
		switch text("operation") {
		case "open":
			var err error
			cold, err = coldprovision.Open(ctx, data("locator"), data("anchor"), text("gateway"), provider.Seed)
			result["handle"] = 0
			if err == nil {
				result["handle"] = 1
			} else {
				test.Log("native bridge open failed", err)
			}
		case "post":
			if cold != nil {
				reply, err := cold.Post(text("path"), []byte(text("body")), text("id"))
				if err == nil {
					result["reply"] = reply
				} else {
					test.Log("native bridge post failed", err)
				}
			}
		case "close":
			if cold != nil {
				cold.Close()
				cold = nil
			}
		case "validate":
			result["code"] = wholedevice.DeliveryValidationCode(data("raw"), data("identity"), data("anchor"), time.Now())
		case "begin":
			secret := data("identity")
			defer clear(secret)
			profile, directory, err := wholedevice.DeliveryMaterial(data("raw"), secret, data("anchor"), time.Now())
			defer clear(profile)
			result["handle"] = 0
			if err == nil {
				physical := Provider{Address: provider.Address, DialContext: network.DialContext}
				session, err = wholedevice.OpenProvisionedWithTransport(ctx, profile, directory, network, func(string) {}, wholedevice.PacketTransport{Seed: physical.Seed, Dedicated: physical.Gateway})
			}
			if err == nil {
				phase = 1
				result["handle"] = 1
			} else {
				test.Log("native bridge begin failed", err)
			}
		case "state", "stats":
			if session == nil || session.Failed() {
				phase = -1
			}
			result["state"] = phase
		case "attach":
			result["accepted"] = session != nil && !session.Failed()
			if result["accepted"] == true {
				phase = 2
			}
		case "stop":
			if session != nil {
				session.Close()
			}
			result["stopped"] = session == nil || session.Failed()
			phase = -1
		case "traffic":
			err := pipelineTraffic(ctx, session, origin)
			result["passed"] = err == nil
			if err != nil {
				test.Log("native bridge traffic failed", err)
			}
		default:
			writer.WriteHeader(400)
			return
		}
		json.NewEncoder(writer).Encode(result)
	}))
	defer server.Close()
	defer func() {
		if cold != nil {
			cold.Close()
		}
		if session != nil {
			session.Close()
		}
	}()
	for _, mode := range []string{"identity", "late", "normal"} {
		command := exec.CommandContext(ctx, java, "-Xmx128m", "-XX:ActiveProcessorCount=1", fmt.Sprintf("-Dfixture.late=%t", mode != "normal"), fmt.Sprintf("-Dfixture.identityChanged=%t", mode == "identity"), fmt.Sprintf("-Dfixture.blackhole=%t", mode == "normal"), "-Dfixture.client="+clientState+mode, "-Dfixture.assets="+assets, "-Dfixture.identity="+filepath.Join(root, "identity96.private"), "-Dfixture.bridge="+server.URL, "-cp", classpath, "com.familyconnect.app.ClientPipeline")
		output, err := command.CombinedOutput()
		if err != nil {
			test.Fatalf("Android source pipeline: %v\n%s", err, output)
		}
		test.Log(string(output))
	}
}
