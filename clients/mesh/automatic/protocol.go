package automatic

import (
	"bytes"
	"encoding/json"
	"io"
	"slices"
	"strings"

	"github.com/Joker20380/family_connect/carrier/desktopauto"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

const Schema = 1
const MaxFrame = 32 << 10
const maxIdentifier = 1<<53 - 1

type Command struct {
	Schema     int                   `json:"schema"`
	ID         uint64                `json:"id"`
	Action     string                `json:"action"`
	Generation uint64                `json:"generation,omitempty"`
	Preferred  desktopauto.Candidate `json:"preferred,omitempty"`
	LastGood   desktopauto.Candidate `json:"last_good,omitempty"`
	Network    *bool                 `json:"network,omitempty"`
	Reason     desktopauto.Failure   `json:"reason,omitempty"`
	Healthy    *bool                 `json:"healthy,omitempty"`
}

type HostReply struct {
	Schema             int                     `json:"schema"`
	ID                 uint64                  `json:"id"`
	OK                 *bool                   `json:"ok"`
	Candidates         []desktopauto.Candidate `json:"candidates,omitempty"`
	Failure            desktopauto.Failure     `json:"failure,omitempty"`
	TemporaryBootstrap bool                    `json:"temporary_bootstrap,omitempty"`
}

type Incoming struct {
	Command *Command   `json:"command,omitempty"`
	Host    *HostReply `json:"host_reply,omitempty"`
}

type HostCall struct {
	Schema     int                   `json:"schema"`
	ID         uint64                `json:"id"`
	Operation  string                `json:"operation"`
	Candidate  desktopauto.Candidate `json:"candidate,omitempty"`
	BudgetMS   int64                 `json:"budget_ms"`
	Generation uint64                `json:"generation"`
}

type HostCancel struct {
	Schema int    `json:"schema"`
	ID     uint64 `json:"id"`
}

type Reply struct {
	Schema   int                  `json:"schema"`
	ID       uint64               `json:"id"`
	OK       bool                 `json:"ok"`
	Error    string               `json:"error,omitempty"`
	Snapshot desktopauto.Snapshot `json:"snapshot"`
}

func validCandidate(candidate desktopauto.Candidate) bool {
	return candidate == "" || candidate == desktopauto.WG || candidate == desktopauto.AWG || candidate == desktopauto.TCP || candidate == desktopauto.Restricted
}

func validFailure(reason desktopauto.Failure) bool {
	switch reason {
	case desktopauto.Cancelled, desktopauto.Auth, desktopauto.Configuration, desktopauto.Network,
		desktopauto.TransportUnavailable, desktopauto.BootstrapUnavailable, desktopauto.Internal:
		return true
	}
	return false
}

func read(input io.Reader) (Incoming, error) {
	var envelope map[string]json.RawMessage
	if worker.ReadControlMessage(input, &envelope, MaxFrame) != nil || len(envelope) != 1 {
		return Incoming{}, worker.ErrProtocol
	}
	var frame Incoming
	var fields map[string]json.RawMessage
	if raw, exists := envelope["command"]; exists {
		frame.Command = &Command{}
		if json.Unmarshal(raw, &fields) != nil || !exactFields(fields, "schema id action generation preferred last_good network reason healthy") || json.Unmarshal(raw, frame.Command) != nil {
			return Incoming{}, worker.ErrProtocol
		}
	} else if raw, exists := envelope["host_reply"]; exists {
		frame.Host = &HostReply{}
		if json.Unmarshal(raw, &fields) != nil || !exactFields(fields, "schema id ok candidates failure temporary_bootstrap") || json.Unmarshal(raw, frame.Host) != nil {
			return Incoming{}, worker.ErrProtocol
		}
	} else {
		return Incoming{}, worker.ErrProtocol
	}
	if command := frame.Command; command != nil {
		if command.Schema != Schema || command.ID == 0 || command.ID > maxIdentifier || command.Generation > maxIdentifier ||
			!validCandidate(command.Preferred) || !validCandidate(command.LastGood) {
			return Incoming{}, worker.ErrProtocol
		}
		valid := false
		allowed := "schema id action generation"
		switch command.Action {
		case "connect":
			allowed += " network preferred last_good"
			valid = command.Generation > 0 && command.Network != nil && command.Healthy == nil && command.Reason == ""
		case "status":
			allowed = "schema id action"
			valid = command.Generation == 0 && command.Network == nil && command.Healthy == nil && command.Reason == ""
		case "network":
			allowed += " network"
			valid = command.Generation > 0 && command.Network != nil && command.Healthy == nil && command.Reason == ""
		case "disconnect", "retry":
			valid = command.Generation > 0 && command.Network == nil && command.Healthy == nil && command.Reason == ""
		case "lost":
			allowed += " reason"
			valid = command.Generation > 0 && command.Network == nil && command.Healthy == nil && validFailure(command.Reason)
		case "healthy":
			allowed += " healthy"
			valid = command.Generation > 0 && command.Network == nil && command.Healthy != nil && command.Reason == ""
		}
		if !valid || !exactFields(fields, allowed) {
			return Incoming{}, worker.ErrProtocol
		}
	} else {
		reply := frame.Host
		if reply.Schema != Schema || reply.ID == 0 || reply.ID > maxIdentifier || reply.OK == nil || len(reply.Candidates) > 3 ||
			(*reply.OK && (reply.Failure != "" || reply.TemporaryBootstrap)) ||
			(!*reply.OK && (!validFailure(reply.Failure) || len(reply.Candidates) != 0)) ||
			(reply.TemporaryBootstrap && reply.Failure != desktopauto.BootstrapUnavailable) {
			return Incoming{}, worker.ErrProtocol
		}
		seen := map[desktopauto.Candidate]bool{}
		for _, candidate := range reply.Candidates {
			if candidate == "" || candidate == desktopauto.Restricted || !validCandidate(candidate) || seen[candidate] {
				return Incoming{}, worker.ErrProtocol
			}
			seen[candidate] = true
		}
	}
	return frame, nil
}

func exactFields(fields map[string]json.RawMessage, allowed string) bool {
	if len(fields) == 0 {
		return false
	}
	names := strings.Fields(allowed)
	for name, value := range fields {
		if !slices.Contains(names, name) || bytes.Equal(bytes.TrimSpace(value), []byte("null")) {
			return false
		}
	}
	return true
}

func encoded(output io.Writer, field string, value any) error {
	frame := map[string]any{field: value}
	raw, err := json.Marshal(frame)
	if err != nil || len(raw) > MaxFrame {
		return worker.ErrProtocol
	}
	return worker.WriteControlReply(output, frame)
}
