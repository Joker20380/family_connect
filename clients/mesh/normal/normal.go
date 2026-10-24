package normal

import (
	"bytes"
	"context"
	"crypto/ecdh"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"slices"
	"strings"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

const Schema = 1
const MaxRequest = 192 << 10

type Command struct {
	Schema           int               `json:"schema"`
	ID               uint64            `json:"id"`
	Action           string            `json:"action"`
	Identity         []byte            `json:"identity,omitempty"`
	Public           []byte            `json:"public,omitempty"`
	Wireguard        []byte            `json:"wireguard_public,omitempty"`
	WireguardPrivate []byte            `json:"wireguard_private,omitempty"`
	Anchor           []byte            `json:"anchor"`
	Country          string            `json:"country"`
	Floors           []json.RawMessage `json:"floors,omitempty"`
	Response         json.RawMessage   `json:"response,omitempty"`
	UnderlyingIndex  int               `json:"underlying_index,omitempty"`
	BudgetMS         int64             `json:"budget_ms,omitempty"`
}

func (Command) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[normal command redacted]") }

func (command *Command) clear() {
	clear(command.Identity)
	clear(command.Public)
	clear(command.Wireguard)
	clear(command.WireguardPrivate)
	clear(command.Anchor)
	clear(command.Response)
	for _, floor := range command.Floors {
		clear(floor)
	}
}

type Reply struct {
	Schema   int             `json:"schema"`
	ID       uint64          `json:"id"`
	OK       bool            `json:"ok"`
	Code     string          `json:"code"`
	Response json.RawMessage `json:"response,omitempty"`
	Catalog  json.RawMessage `json:"catalog,omitempty"`
	Sequence uint64          `json:"sequence,omitempty"`
	Digest   string          `json:"digest,omitempty"`
	Public   []byte          `json:"public,omitempty"`
}

func (Reply) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[normal response redacted]") }

type Protector interface{ Protect(net.Interface, int) bool }
type environment struct {
	lookup func(int) (*net.Interface, error)
	open   func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error)
}

func production() environment {
	return environment{lookup: net.InterfaceByIndex, open: func(ctx context.Context, link net.Interface, platform Protector) (desktopmesh.ReadinessTransport, func(), error) {
		network, err := underlay.New(ctx, "1.1.1.1:53", func(descriptor int) bool { return platform.Protect(link, descriptor) })
		if err != nil {
			return nil, nil, err
		}
		transport, err := desktopmesh.NewNormalHTTPS(network)
		if err != nil {
			network.Close()
			return nil, nil, err
		}
		return transport, func() { transport.Close(); network.Close() }, nil
	}}
}

func code(err error) string {
	var failure *desktopmesh.ReadinessFailure
	switch {
	case errors.Is(err, context.Canceled):
		return "CANCELLED"
	case errors.Is(err, context.DeadlineExceeded):
		return "NETWORK"
	case errors.As(err, &failure):
		if failure.Authorization || failure.Code == "TLS_TRUST_REJECTED" {
			return "AUTH"
		}
		if failure.Availability || failure.Network {
			return "NETWORK"
		}
		return "CONFIGURATION"
	case errors.Is(err, desktopmesh.ErrConfiguration), errors.Is(err, desktopmesh.ErrClosed):
		return "CONFIGURATION"
	default:
		return "INTERNAL"
	}
}

func prepare(ctx context.Context, command *Command, platform Protector, runtime environment) Reply {
	reply := Reply{Schema: Schema, ID: command.ID, Code: "CONFIGURATION"}
	if command.Schema != Schema || command.ID == 0 || command.ID > desktopmesh.MaxNormalSequence || len(command.Anchor) != 32 ||
		(command.Country != "ru" && command.Country != "nl") || len(command.Floors) > 3 {
		return reply
	}
	if ctx.Err() != nil {
		reply.Code = code(ctx.Err())
		return reply
	}
	var configured desktopmesh.NormalConfiguration
	var err error
	if command.Action == "inspect" {
		if len(command.Public) != 64 || len(command.Identity) != 0 || len(command.Wireguard) != 0 || len(command.WireguardPrivate) != 0 || command.BudgetMS != 0 || command.UnderlyingIndex != 0 {
			return reply
		}
		digest := sha256.Sum256(command.Public)
		configured, err = desktopmesh.VerifyNormalResponse(command.Response, command.Anchor, hex.EncodeToString(digest[:16]), command.Country, command.Floors)
		reply.Public = bytes.Clone(command.Public)
	} else if command.Action == "fetch" || command.Action == "validate" {
		if len(command.Identity) != 64 || len(command.Wireguard) != 32 || len(command.WireguardPrivate) != 32 || len(command.Public) != 0 || len(command.Response) != 0 ||
			(command.Action == "fetch" && (command.UnderlyingIndex <= 0 || command.BudgetMS <= 0 || command.BudgetMS > 30000 || platform == nil)) ||
			(command.Action == "validate" && (command.UnderlyingIndex != 0 || command.BudgetMS != 0)) {
			return reply
		}
		wireguard, failure := ecdh.X25519().NewPrivateKey(command.WireguardPrivate)
		if failure != nil || !bytes.Equal(wireguard.PublicKey().Bytes(), command.Wireguard) {
			return reply
		}
		client, failure := desktopmesh.NewReadinessClient(command.Identity, command.Wireguard)
		if failure != nil {
			return reply
		}
		defer client.Close()
		if _, _, failure := desktopmesh.VerifyNormalFloors(command.Floors, command.Anchor); failure != nil {
			return reply
		}
		if command.Action == "validate" {
			if ctx.Err() != nil {
				reply.Code = code(ctx.Err())
				return reply
			}
			reply.OK, reply.Code, reply.Public = true, "VALIDATED_MATERIAL", client.Public()
			return reply
		}
		link, failure := runtime.lookup(command.UnderlyingIndex)
		if failure != nil || link == nil || link.Index != command.UnderlyingIndex || link.Flags&net.FlagUp == 0 || link.Flags&net.FlagLoopback != 0 ||
			link.Name == worker.InterfaceName || strings.HasPrefix(link.Name, "fcawg") || strings.HasPrefix(link.Name, "fctcp") {
			reply.Code = "NETWORK"
			return reply
		}
		bounded, cancel := context.WithTimeout(ctx, time.Duration(command.BudgetMS)*time.Millisecond)
		defer cancel()
		transport, closeNetwork, failure := runtime.open(bounded, *link, platform)
		if closeNetwork != nil {
			defer closeNetwork()
		}
		if failure != nil {
			reply.Code = "CONFIGURATION"
			return reply
		}
		configured, err = client.FetchNormal(bounded, transport, command.Country, command.Anchor, command.Floors)
		if bounded.Err() != nil {
			err = bounded.Err()
		}
		reply.Public = client.Public()
	} else {
		return reply
	}
	if ctx.Err() != nil {
		err = ctx.Err()
	}
	defer configured.Clear()
	if err != nil {
		reply.Code = code(err)
		clear(reply.Public)
		reply.Public = nil
		return reply
	}
	reply.OK, reply.Code = true, "AUTHENTICATED_RESPONSE"
	reply.Response, reply.Catalog = bytes.Clone(configured.Response), bytes.Clone(configured.Catalog)
	reply.Sequence, reply.Digest = configured.Sequence, configured.Digest
	return reply
}

func read(input io.Reader, command *Command) error {
	var fields map[string]json.RawMessage
	if worker.ReadControlMessage(input, &fields, MaxRequest) != nil {
		return worker.ErrProtocol
	}
	defer func() {
		for _, value := range fields {
			clear(value)
		}
	}()
	var action string
	if json.Unmarshal(fields["action"], &action) != nil {
		return worker.ErrProtocol
	}
	allowed := "schema id action anchor country floors "
	if action == "fetch" {
		allowed += "identity wireguard_public wireguard_private underlying_index budget_ms"
	} else if action == "validate" {
		allowed += "identity wireguard_public wireguard_private"
	} else if action == "inspect" {
		allowed += "public response"
	} else {
		return worker.ErrProtocol
	}
	for name, value := range fields {
		if !slices.Contains(strings.Fields(allowed), name) || bytes.Equal(bytes.TrimSpace(value), []byte("null")) {
			return worker.ErrProtocol
		}
	}
	raw, err := json.Marshal(fields)
	defer clear(raw)
	if err != nil || json.Unmarshal(raw, command) != nil {
		return worker.ErrProtocol
	}
	return nil
}

func Serve(ctx context.Context, input io.Reader, output io.Writer, platform Protector) error {
	var command Command
	defer command.clear()
	if err := read(input, &command); err != nil {
		return err
	}
	reply := prepare(ctx, &command, platform, production())
	defer clear(reply.Response)
	defer clear(reply.Catalog)
	defer clear(reply.Public)
	return worker.WriteControlReply(output, reply)
}
