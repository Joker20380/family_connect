package chatipc

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

const Schema = 1
const MaxJobs = 12
const MaxStreams = 4
const MaxFrame = 96 << 10
const MaxData = 16 << 10

type Acquisition struct {
	Readiness       json.RawMessage `json:"readiness"`
	Identity        []byte          `json:"identity"`
	Anchor          []byte          `json:"anchor"`
	Resolver        string          `json:"resolver"`
	UnderlyingIndex int             `json:"underlying_index"`
}

func (material *Acquisition) erase() {
	if material != nil {
		clear(material.Readiness)
		clear(material.Identity)
		clear(material.Anchor)
	}
}

type Request struct {
	Schema   int          `json:"schema"`
	ID       uint64       `json:"id"`
	Action   string       `json:"action"`
	Acquire  *Acquisition `json:"acquire,omitempty"`
	Lease    uint64       `json:"lease,omitempty"`
	Stream   uint64       `json:"stream,omitempty"`
	BudgetMS int64        `json:"budget_ms,omitempty"`
	Path     string       `json:"path,omitempty"`
	Data     []byte       `json:"data,omitempty"`
	Size     int          `json:"size,omitempty"`
	Target   uint64       `json:"target,omitempty"`
}

func (request Request) erase()                     { request.Acquire.erase(); clear(request.Data) }
func (Request) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[chat IPC request redacted]") }
func (Acquisition) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[chat IPC material redacted]")
}

func readRequest(input io.Reader) (Request, error) {
	var request Request
	err := worker.ReadControlMessage(input, &request, MaxFrame)
	if err != nil || !request.valid() {
		request.erase()
		if err == io.EOF {
			return Request{}, err
		}
		return Request{}, worker.ErrProtocol
	}
	return request, nil
}

func (request Request) valid() bool {
	if request.Schema != Schema || request.ID == 0 {
		return false
	}
	remaining := request
	remaining.Schema, remaining.ID, remaining.Action = 0, 0, ""
	if request.Action == "acquire" || request.Action == "request" || request.Action == "open" || request.Action == "read" || request.Action == "write" || request.Action == "finish" {
		if request.BudgetMS <= 0 || request.BudgetMS > 30000 {
			return false
		}
		remaining.BudgetMS = 0
	}
	switch request.Action {
	case "acquire":
		material := request.Acquire
		if material == nil || len(material.Readiness) == 0 || len(material.Readiness) > wholedevice.MaxReadiness || len(material.Identity) != 64 || len(material.Anchor) != 32 || material.UnderlyingIndex <= 0 {
			return false
		}
		host, port, err := net.SplitHostPort(material.Resolver)
		if err != nil || net.ParseIP(host).To4() == nil || port != "53" {
			return false
		}
		remaining.Acquire = nil
	case "route", "release", "open", "request":
		if request.Lease == 0 {
			return false
		}
		remaining.Lease = 0
		if request.Action == "request" {
			if (request.Path != "/friends/chat/challenge" && request.Path != "/friends/chat/register") || len(request.Data) > restrictedchat.MaxRequest {
				return false
			}
			remaining.Path, remaining.Data = "", nil
		}
	case "read", "write", "finish", "close":
		if request.Stream == 0 {
			return false
		}
		remaining.Stream = 0
		if request.Action == "read" {
			if request.Size <= 0 || request.Size > MaxData {
				return false
			}
			remaining.Size = 0
		}
		if request.Action == "write" {
			if len(request.Data) == 0 || len(request.Data) > MaxData {
				return false
			}
			remaining.Data = nil
		}
	case "cancel":
		if request.Target == 0 || request.Target >= request.ID {
			return false
		}
		remaining.Target = 0
	default:
		return false
	}
	return remaining.Acquire == nil && remaining.Lease == 0 && remaining.Stream == 0 && remaining.BudgetMS == 0 && remaining.Path == "" && len(remaining.Data) == 0 && remaining.Size == 0 && remaining.Target == 0
}

type Reply struct {
	Schema int    `json:"schema"`
	ID     uint64 `json:"id"`
	OK     bool   `json:"ok"`
	Error  string `json:"error,omitempty"`
	Lease  uint64 `json:"lease,omitempty"`
	Stream uint64 `json:"stream,omitempty"`
	Route  string `json:"route,omitempty"`
	Status int    `json:"status,omitempty"`
	Data   []byte `json:"data,omitempty"`
	Count  int    `json:"count,omitempty"`
	EOF    bool   `json:"eof,omitempty"`
}

func (Reply) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[chat IPC reply redacted]") }

func writeReply(output io.Writer, reply Reply) error {
	raw, err := json.Marshal(reply)
	if err != nil || len(raw) > MaxFrame {
		return worker.ErrProtocol
	}
	defer clear(raw)
	var header [4]byte
	binary.BigEndian.PutUint32(header[:], uint32(len(raw)))
	for _, data := range [][]byte{header[:], raw} {
		for len(data) > 0 {
			count, err := output.Write(data)
			if err != nil {
				return err
			}
			if count == 0 {
				return io.ErrShortWrite
			}
			data = data[count:]
		}
	}
	return nil
}
