//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"io"
	"strings"
)

type correlationRequest struct {
	Operation  string                 `json:"operation"`
	Key        CorrelationKey         `json:"key"`
	Descriptor *CorrelationDescriptor `json:"descriptor,omitempty"`
}

func (recorder *Recorder) CorrelationCommand(raw, role string) string {
	const rejected = `{"error":"rejected"}`
	if recorder == nil || len(raw) > 16*1024 || !Allowed(role, "client|gateway") {
		return rejected
	}
	decoder := json.NewDecoder(strings.NewReader(raw))
	decoder.DisallowUnknownFields()
	var request correlationRequest
	if decoder.Decode(&request) != nil {
		return rejected
	}
	var trailing any
	if decoder.Decode(&trailing) != io.EOF {
		return rejected
	}
	local := "rx"
	if (role == "client" && request.Key.Direction == "client_to_gateway") || (role == "gateway" && request.Key.Direction == "gateway_to_client") {
		local = "tx"
	}
	var receipt CorrelationReceipt
	var err error
	switch request.Operation {
	case "prearm":
		receipt, err = recorder.PrearmCorrelation(request.Key, local)
	case "status", "cleanup":
		receipt, err = recorder.CorrelationStatus(request.Key, request.Operation == "cleanup")
	case "bind":
		if request.Descriptor == nil || request.Descriptor.Key != request.Key || local != "rx" {
			return rejected
		}
		receipt, err = recorder.BindCorrelation(*request.Descriptor)
	default:
		return rejected
	}
	if err != nil {
		return rejected
	}
	encoded, err := json.Marshal(receipt)
	if err != nil {
		return rejected
	}
	return string(encoded)
}
