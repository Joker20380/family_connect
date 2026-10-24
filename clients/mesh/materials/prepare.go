package materials

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type Command struct {
	Schema          int                           `json:"schema"`
	ID              uint64                        `json:"id"`
	Action          string                        `json:"action"`
	Identity        []byte                        `json:"identity,omitempty"`
	Public          []byte                        `json:"public,omitempty"`
	Wireguard       []byte                        `json:"wireguard_public,omitempty"`
	Anchor          []byte                        `json:"anchor"`
	Cached          json.RawMessage               `json:"cached,omitempty"`
	Attempt         *desktopmesh.ReadinessAttempt `json:"attempt,omitempty"`
	UnderlyingIndex int                           `json:"underlying_index,omitempty"`
	BudgetMS        int64                         `json:"budget_ms,omitempty"`
	Required        bool                          `json:"required,omitempty"`
	Phase           string                        `json:"phase,omitempty"`
	AppVersion      string                        `json:"app_version,omitempty"`
	VersionCode     int64                         `json:"version_code,omitempty"`
	ImportResult    desktopmesh.ReadinessCode     `json:"import_result,omitempty"`
	Receipt         json.RawMessage               `json:"receipt,omitempty"`
}

func (Command) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[readiness command redacted]")
}

func (command *Command) erase() {
	clear(command.Identity)
	clear(command.Public)
	clear(command.Wireguard)
	clear(command.Anchor)
	clear(command.Cached)
	clear(command.Receipt)
}

type Reply struct {
	Schema          int                           `json:"schema"`
	ID              uint64                        `json:"id"`
	OK              bool                          `json:"ok"`
	Code            string                        `json:"code"`
	Source          desktopmesh.ReadinessSource   `json:"source,omitempty"`
	Reference       string                        `json:"device,omitempty"`
	Public          []byte                        `json:"public,omitempty"`
	Validated       bool                          `json:"validated"`
	Durable         bool                          `json:"durable"`
	StorageRequired bool                          `json:"storage_required"`
	CandidateSHA256 string                        `json:"candidate_sha256,omitempty"`
	CacheProposal   []byte                        `json:"cache_proposal,omitempty"`
	RelayAvailable  bool                          `json:"relay_available"`
	ImportResult    desktopmesh.ReadinessCode     `json:"import_result,omitempty"`
	Receipt         *desktopmesh.ReadinessReceipt `json:"receipt,omitempty"`
}

func (Reply) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[readiness proposal redacted]") }

type memoryStorage struct {
	raw   []byte
	dirty bool
}

func (storage *memoryStorage) Read() ([]byte, error) { return bytes.Clone(storage.raw), nil }

func (storage *memoryStorage) Write(raw []byte) error {
	storage.dirty = storage.dirty || !bytes.Equal(storage.raw, raw)
	clear(storage.raw)
	storage.raw = bytes.Clone(raw)
	return nil
}

type Protector interface {
	Protect(net.Interface, int) bool
}

func valid(command *Command) bool {
	if command.Schema != 1 || command.ID == 0 || command.ID >= 1<<63 || len(command.Anchor) != 32 || len(command.Cached) > desktopmesh.MaxReadinessCache {
		return false
	}
	private := len(command.Public) == 0 && len(command.Identity) == 64 && len(command.Wireguard) == 32
	if command.Action == "receipt" {
		if !private || command.UnderlyingIndex != 0 || command.BudgetMS != 0 || command.Required || command.Attempt == nil || !command.Attempt.Valid() || len(command.Receipt) != 0 {
			return false
		}
		code := command.ImportResult
		if code == "" {
			code = desktopmesh.ReadinessMissing
		}
		_, err := desktopmesh.FailureReadinessReceipt(*command.Attempt, time.Now(), command.Phase, command.AppVersion, command.VersionCode, code)
		return err == nil && (command.Phase == "import" || command.ImportResult == "")
	}
	if command.Phase != "" || command.AppVersion != "" || command.VersionCode != 0 || command.ImportResult != "" {
		return false
	}
	if command.Action == "ack" {
		_, err := desktopmesh.DecodeReadinessReceipt(command.Receipt)
		return private && len(command.Cached) == 0 && command.Attempt == nil && !command.Required &&
			command.UnderlyingIndex > 0 && command.BudgetMS > 0 && command.BudgetMS <= 15000 && err == nil
	}
	if len(command.Receipt) != 0 {
		return false
	}
	if command.Action == "inspect" {
		return len(command.Public) == 64 && len(command.Identity) == 0 && len(command.Wireguard) == 0 && command.UnderlyingIndex == 0 && command.BudgetMS == 0 && command.Attempt == nil && !command.Required
	}
	return command.Action == "refresh" && len(command.Public) == 0 && len(command.Identity) == 64 && len(command.Wireguard) == 32 &&
		command.UnderlyingIndex > 0 && command.BudgetMS > 0 && command.BudgetMS <= 200000 && command.Attempt != nil && command.Attempt.Valid()
}

func failureCode(err error) string {
	var code desktopmesh.ReadinessCode
	var failure *desktopmesh.ReadinessFailure
	switch {
	case err == nil:
		return "READY"
	case errors.Is(err, context.Canceled):
		return "CANCELLED"
	case errors.Is(err, context.DeadlineExceeded):
		return "DEADLINE"
	case errors.As(err, &code):
		return string(code)
	case errors.As(err, &failure):
		return failure.Code
	default:
		return "READINESS_FAILED"
	}
}

type preparationEnvironment struct {
	lookup func(int) (*net.Interface, error)
	open   func(context.Context, net.Interface, Protector) (desktopmesh.ReadinessTransport, func(), error)
	relay  func(context.Context, int) *relayProcess
}

func Prepare(ctx context.Context, command *Command, platform Protector) Reply {
	return prepare(ctx, command, platform, preparationEnvironment{lookup: net.InterfaceByIndex, relay: installedRelay,
		open: func(ctx context.Context, underlying net.Interface, platform Protector) (desktopmesh.ReadinessTransport, func(), error) {
			network, err := underlay.New(ctx, "1.1.1.1:53", func(descriptor int) bool { return platform.Protect(underlying, descriptor) })
			if err != nil {
				return nil, nil, err
			}
			transport, err := desktopmesh.NewReadinessHTTPS(network)
			return transport, network.Close, err
		}})
}

func prepare(ctx context.Context, command *Command, platform Protector, environment preparationEnvironment) Reply {
	reply := Reply{Schema: 1, Code: "INVALID_MATERIALS_COMMAND"}
	if command == nil {
		return reply
	}
	reply.ID = command.ID
	if !valid(command) {
		return reply
	}
	if ctx.Err() != nil {
		reply.Code = failureCode(ctx.Err())
		return reply
	}
	storage := &memoryStorage{}
	if len(command.Cached) != 0 && !bytes.Equal(bytes.TrimSpace(command.Cached), []byte("null")) {
		storage.raw = bytes.Clone(command.Cached)
	}
	defer func() { clear(storage.raw) }()
	public := command.Public
	var client *desktopmesh.ReadinessClient
	var err error
	if command.Action != "inspect" {
		client, err = desktopmesh.NewReadinessClient(command.Identity, command.Wireguard)
		if err != nil {
			return reply
		}
		defer client.Close()
		public = client.Public()
		defer clear(public)
	}
	digest := sha256.Sum256(public)
	reply.Reference = hex.EncodeToString(digest[:16])
	reply.Public = bytes.Clone(public)
	cache, err := desktopmesh.NewReadinessCache(storage, public, command.Anchor)
	if err != nil {
		return reply
	}
	if command.Action == "inspect" {
		raw, code := cache.Usable(time.Now())
		clear(raw)
		reply.Code, reply.OK, reply.Validated = string(code), true, code == desktopmesh.ReadinessReady
		if ctx.Err() != nil {
			reply.Code, reply.OK, reply.Validated = failureCode(ctx.Err()), false, false
		}
		return reply
	}
	if command.Action == "receipt" {
		var receipt desktopmesh.ReadinessReceipt
		if command.ImportResult == "" {
			receipt, err = cache.Receipt(*command.Attempt, time.Now(), command.Phase, command.AppVersion, command.VersionCode)
		} else {
			receipt, err = desktopmesh.FailureReadinessReceipt(*command.Attempt, time.Now(), command.Phase, command.AppVersion, command.VersionCode, command.ImportResult)
		}
		if err == nil && ctx.Err() == nil {
			reply.OK, reply.Code, reply.Receipt = true, "RECEIPT_READY", &receipt
		} else if ctx.Err() != nil {
			reply.Code = failureCode(ctx.Err())
		}
		return reply
	}
	underlying, err := environment.lookup(command.UnderlyingIndex)
	if err != nil || underlying == nil || underlying.Flags&net.FlagUp == 0 || underlying.Flags&net.FlagLoopback != 0 || underlying.Name == worker.InterfaceName || platform == nil {
		reply.Code = "UNDERLAY_UNAVAILABLE"
		return reply
	}
	ctx, cancel := context.WithTimeout(ctx, time.Duration(command.BudgetMS)*time.Millisecond)
	defer cancel()
	transport, closeNetwork, err := environment.open(ctx, *underlying, platform)
	if closeNetwork != nil {
		defer closeNetwork()
	}
	if err != nil {
		reply.Code = "UNDERLAY_UNAVAILABLE"
		return reply
	}
	if environment.relay != nil {
		if process := environment.relay(ctx, underlying.Index); process != nil {
			defer process.Close()
			relay, _ := desktopmesh.NewReadinessRelay(process.request)
			transport, _ = desktopmesh.NewReadinessRoute(transport, relay)
			reply.RelayAvailable = true
		}
	}
	if command.Action == "ack" {
		receipt, _ := desktopmesh.DecodeReadinessReceipt(command.Receipt)
		err := client.Acknowledge(ctx, transport, receipt)
		reply.OK, reply.Code = err == nil, failureCode(err)
		if err == nil {
			reply.Code = "ACK_RECEIVED"
		}
		return reply
	}
	raw, source, result, err := desktopmesh.ResolveReadinessWithResult(ctx, cache, client, transport, *command.Attempt, command.Required)
	clear(raw)
	reply.ImportResult = result
	reply.Code, reply.Source = failureCode(err), source
	reply.OK, reply.Validated = err == nil, err == nil
	if storage.dirty {
		reply.StorageRequired = true
		reply.CacheProposal = bytes.Clone(storage.raw)
		digest = sha256.Sum256(storage.raw)
		reply.CandidateSHA256 = hex.EncodeToString(digest[:])
	}
	return reply
}

func Serve(ctx context.Context, input io.Reader, output io.Writer, platform Protector) error {
	var command Command
	defer command.erase()
	if err := worker.ReadControlRequest(input, &command); err != nil {
		return err
	}
	reply := Prepare(ctx, &command, platform)
	defer clear(reply.CacheProposal)
	return worker.WriteControlReply(output, reply)
}
