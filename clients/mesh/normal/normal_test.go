package normal

import (
	"bytes"
	"context"
	"crypto/ecdh"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type protector struct{}

func (protector) Protect(net.Interface, int) bool { return false }

func validCommand() Command {
	private := bytes.Repeat([]byte{1}, 32)
	key, _ := ecdh.X25519().NewPrivateKey(private)
	return Command{Schema: 1, ID: 1, Action: "fetch", Identity: bytes.Repeat([]byte{2}, 64), Wireguard: key.PublicKey().Bytes(), WireguardPrivate: private, Anchor: bytes.Repeat([]byte{3}, 32), Country: "nl", UnderlyingIndex: 2, BudgetMS: 1000}
}

func TestConfigurationCannotSelectPathsNetworksOrActions(test *testing.T) {
	for _, body := range []string{
		`{}`, `{"schema":1,"id":1,"action":"exec"}`, `{"schema":1,"id":1,"action":"fetch","URL":"https://bad"}`,
		`{"schema":1,"id":1,"action":"fetch","Schema":1}`, `{"schema":1,"id":1,"id":2,"action":"fetch"}`,
		`{"schema":1,"id":1,"action":"fetch","floors":null}`, `{"schema":1,"id":1,"action":"inspect","identity":"AA=="}`,
		strings.Repeat("x", MaxRequest+1),
	} {
		var frame bytes.Buffer
		binary.Write(&frame, binary.BigEndian, uint32(len(body)))
		frame.WriteString(body)
		var command Command
		if err := read(&frame, &command); !errors.Is(err, worker.ErrProtocol) {
			test.Fatal("invalid wire accepted")
		}
		command.clear()
	}
}

func TestRejectedCredentialNeverTouchesUnderlyingNetwork(test *testing.T) {
	for _, mutate := range []func(*Command){
		func(command *Command) { command.Wireguard[0] ^= 1 }, func(command *Command) { command.WireguardPrivate = nil },
		func(command *Command) { command.Identity = nil }, func(command *Command) { command.Country = "../ru" },
		func(command *Command) { command.BudgetMS = 30001 }, func(command *Command) { command.Floors = []json.RawMessage{json.RawMessage(`{}`)} },
	} {
		command := validCommand()
		mutate(&command)
		reply := prepare(context.Background(), &command, protector{}, environment{lookup: func(int) (*net.Interface, error) { test.Fatal("network touched"); return nil, nil }})
		if reply.OK || reply.Code != "CONFIGURATION" || len(reply.Response) != 0 {
			test.Fatal("invalid configuration accepted")
		}
		command.clear()
	}
}

func TestConfigurationProtectsRealUnderlyingInterfaceOnly(test *testing.T) {
	for _, link := range []net.Interface{
		{Index: 2, Name: "lo", Flags: net.FlagUp | net.FlagLoopback}, {Index: 2, Name: "fcmesh0", Flags: net.FlagUp},
		{Index: 2, Name: "fcawg12345678", Flags: net.FlagUp}, {Index: 2, Name: "fctcp12345678", Flags: net.FlagUp},
		{Index: 2, Name: "eth0"}, {Index: 3, Name: "eth0", Flags: net.FlagUp},
	} {
		command := validCommand()
		runtime := environment{lookup: func(int) (*net.Interface, error) { return &link, nil }, open: func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error) {
			test.Fatal("unsafe bind")
			return nil, nil, nil
		}}
		if reply := prepare(context.Background(), &command, protector{}, runtime); reply.OK || reply.Code != "NETWORK" {
			test.Fatal("unsafe link accepted")
		}
	}
}

func TestOfflineMaterialValidationCannotAuthorizeOrTouchNetwork(test *testing.T) {
	for _, invalid := range []bool{false, true} {
		command := validCommand()
		command.Action, command.UnderlyingIndex, command.BudgetMS = "validate", 0, 0
		if invalid {
			command.Wireguard[0] ^= 1
		}
		runtime := environment{lookup: func(int) (*net.Interface, error) { test.Fatal("offline validation touched network"); return nil, nil }}
		reply := prepare(context.Background(), &command, nil, runtime)
		if invalid {
			if reply.OK || reply.Code != "CONFIGURATION" {
				test.Fatal("mismatched key accepted offline")
			}
		} else if !reply.OK || reply.Code != "VALIDATED_MATERIAL" || len(reply.Public) != 64 || len(reply.Response) != 0 || len(reply.Catalog) != 0 {
			test.Fatal("offline validation confused with gateway authorization")
		}
		command.clear()
	}
}

func TestNormalErrorsAndFormattingRemainPrivate(test *testing.T) {
	for _, item := range []struct {
		err      error
		expected string
	}{
		{context.Canceled, "CANCELLED"}, {context.DeadlineExceeded, "NETWORK"},
		{&desktopmesh.ReadinessFailure{Code: "AUTHORIZATION_REJECTED", Authorization: true}, "AUTH"},
		{&desktopmesh.ReadinessFailure{Code: "TLS_TRUST_REJECTED"}, "AUTH"},
		{&desktopmesh.ReadinessFailure{Code: "NORMAL_FETCH_REJECTED", Availability: true}, "NETWORK"},
		{errors.New("private token and proof"), "INTERNAL"},
	} {
		if code(item.err) != item.expected {
			test.Fatal("wrong category")
		}
	}
	command := validCommand()
	if text := fmt.Sprintf("%+v", command); text != "[normal command redacted]" {
		test.Fatal("command exposed")
	}
	if text := fmt.Sprintf("%+v", Reply{Response: json.RawMessage(`{"secret":true}`)}); text != "[normal response redacted]" {
		test.Fatal("response exposed")
	}
	command.clear()
	if !bytes.Equal(command.Identity, make([]byte, 64)) || !bytes.Equal(command.WireguardPrivate, make([]byte, 32)) {
		test.Fatal("keys retained")
	}
}
