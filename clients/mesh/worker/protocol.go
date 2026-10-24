package worker

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"unicode/utf8"
)

const Schema = 1
const MaxRequest = 96 << 10
const MaxReply = 512 << 10

var ErrProtocol = errors.New("invalid mesh IPC")

type Start struct {
	Attempt         int64           `json:"attempt"`
	BudgetMS        int64           `json:"budget_ms"`
	Profile         string          `json:"profile"`
	Resolver        string          `json:"resolver"`
	UnderlyingIndex int             `json:"underlying_index"`
	Readiness       json.RawMessage `json:"readiness"`
	Identity        []byte          `json:"identity"`
	Anchor          []byte          `json:"anchor"`
}

func (start *Start) Erase() {
	if start != nil {
		clear(start.Identity)
		clear(start.Readiness)
		clear(start.Anchor)
	}
}
func (Start) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[mesh startup redacted]") }

type Request struct {
	Schema int    `json:"schema"`
	ID     uint64 `json:"id"`
	Action string `json:"action"`
	Start  *Start `json:"start,omitempty"`
}

func (Request) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[mesh command redacted]") }

type Reply struct {
	Schema    int            `json:"schema"`
	ID        uint64         `json:"id"`
	OK        bool           `json:"ok"`
	State     string         `json:"state"`
	Error     string         `json:"error,omitempty"`
	Interface string         `json:"interface,omitempty"`
	MTU       int            `json:"mtu,omitempty"`
	Snapshot  map[string]any `json:"snapshot,omitempty"`
}

func ReadRequest(input io.Reader) (Request, error) {
	var request Request
	if err := ReadControlRequest(input, &request); err != nil {
		request.Start.Erase()
		return Request{}, err
	}
	if request.Schema != Schema || request.ID == 0 {
		request.Start.Erase()
		return Request{}, ErrProtocol
	}
	valid := false
	switch request.Action {
	case "start":
		valid = request.Start != nil
	case "status", "routed", "stop":
		valid = request.Start == nil
	}
	if !valid {
		request.Start.Erase()
		return Request{}, ErrProtocol
	}
	return request, nil
}

func ReadControlRequest(input io.Reader, target any) error {
	return ReadControlMessage(input, target, MaxRequest)
}

func ReadControlMessage(input io.Reader, target any, maximum uint32) error {
	if maximum == 0 || maximum > MaxReply {
		return ErrProtocol
	}
	var size [4]byte
	if _, err := io.ReadFull(input, size[:]); err != nil {
		return err
	}
	length := binary.BigEndian.Uint32(size[:])
	if length == 0 || length > maximum {
		return ErrProtocol
	}
	raw := make([]byte, length)
	defer clear(raw)
	if _, err := io.ReadFull(input, raw); err != nil {
		return ErrProtocol
	}
	if !utf8.Valid(raw) {
		return ErrProtocol
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	if strictValue(decoder, 0) != nil || decoder.Decode(new(any)) != io.EOF {
		return ErrProtocol
	}
	decoder = json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil {
		return ErrProtocol
	}
	return nil
}

func strictValue(decoder *json.Decoder, depth int) error {
	if depth > 16 {
		return ErrProtocol
	}
	token, err := decoder.Token()
	if err != nil {
		return ErrProtocol
	}
	switch token {
	case json.Delim('{'):
		seen := make(map[string]bool)
		for decoder.More() {
			token, err := decoder.Token()
			name, valid := token.(string)
			if err != nil || !valid || seen[name] {
				return ErrProtocol
			}
			seen[name] = true
			if err := strictValue(decoder, depth+1); err != nil {
				return err
			}
		}
		ending, err := decoder.Token()
		if err != nil || ending != json.Delim('}') {
			return ErrProtocol
		}
	case json.Delim('['):
		for decoder.More() {
			if err := strictValue(decoder, depth+1); err != nil {
				return err
			}
		}
		ending, err := decoder.Token()
		if err != nil || ending != json.Delim(']') {
			return ErrProtocol
		}
	case json.Delim('}'), json.Delim(']'):
		return ErrProtocol
	}
	return nil
}

func WriteReply(output io.Writer, reply Reply) error {
	return WriteControlReply(output, reply)
}

func WriteControlReply(output io.Writer, reply any) error {
	raw, err := json.Marshal(reply)
	defer clear(raw)
	if err != nil || len(raw) > MaxReply {
		return ErrProtocol
	}
	var size [4]byte
	binary.BigEndian.PutUint32(size[:], uint32(len(raw)))
	for _, part := range [][]byte{size[:], raw} {
		written, err := output.Write(part)
		if err != nil {
			return err
		}
		if written != len(part) {
			return io.ErrShortWrite
		}
	}
	return nil
}
